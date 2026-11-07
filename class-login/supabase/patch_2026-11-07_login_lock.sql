-- 2026-11-07 패치: 그림 비밀번호 동시 시도로 5회 잠금을 우회하지 못하게 함
-- Supabase 대시보드 → SQL Editor 에 이 파일 내용을 붙여 넣고 Run. 여러 번 실행해도 안전해요.
create or replace function public.cl_student_login(p_code text, p_num int, p_secret text) returns json
language plpgsql volatile security definer set search_path = public, extensions as $$
declare st public.cl_students%rowtype; cl public.cl_classes%rowtype; tok text;
begin
  select * into cl from public.cl_classes where code = upper(trim(coalesce(p_code, '')));
  if not found then return json_build_object('ok', false, 'error', 'no_class'); end if;
  -- for update: 같은 학생에게 동시에 여러 번 시도해도 한 번에 하나씩 확인 (잠금 우회 방지)
  select * into st from public.cl_students where class_id = cl.id and num = p_num for update;
  if not found then return json_build_object('ok', false, 'error', 'no_student'); end if;
  if st.locked_until is not null and st.locked_until > now() then
    return json_build_object('ok', false, 'error', 'locked', 'until', st.locked_until);
  end if;
  if st.secret <> coalesce(p_secret, '') then
    update public.cl_students set fail_count = fail_count + 1,
      locked_until = case when fail_count + 1 >= 5 then now() + interval '5 minutes' else null end
      where id = st.id;
    return json_build_object('ok', false, 'error', 'bad_secret');
  end if;
  update public.cl_students set fail_count = 0, locked_until = null, last_seen = now() where id = st.id;
  delete from public.cl_sessions where student_id = st.id and expires_at < now();
  tok := encode(gen_random_bytes(24), 'hex');
  insert into public.cl_sessions(token, student_id) values (tok, st.id);
  return json_build_object('ok', true, 'token', tok,
    'student', json_build_object('id', st.id, 'num', st.num),
    'class', json_build_object('name', cl.name, 'code', cl.code));
end $$;
