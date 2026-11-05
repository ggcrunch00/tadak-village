-- 이름을 쓰는 섬: 학급 서버 (Supabase)
-- Supabase 대시보드 → SQL Editor 에 이 파일 전체를 붙여 넣고 Run.
-- 여러 번 실행해도 괜찮아요(이미 있는 것은 건너뜀).
--
-- 구조
--   선생님: Supabase 로그인(이메일+비밀번호). 자기 학급만 보고 고칠 수 있음 (RLS).
--   학생:   이메일 없음. 학급 코드 + 번호 + 4자리 비밀번호 → student_login() 이 토큰을 줌.
--           학생은 테이블을 직접 읽지 못하고, 토큰을 받는 함수(student_*)로만 자기 것을 읽고 씀.
--   개인정보: 학생 이름은 선생님이 넣는 표시용 이름(별명 가능). 이메일, 전화번호는 받지 않음.

create extension if not exists pgcrypto with schema extensions;

-- ---------- 테이블 ----------
create table if not exists public.classes (
  id uuid primary key default gen_random_uuid(),
  teacher_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  name text not null check (char_length(name) between 1 and 40),
  code text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  class_id uuid not null references public.classes(id) on delete cascade,
  num int not null check (num between 1 and 99),
  name text not null check (char_length(name) between 1 and 20),
  pin_hash text not null,
  fail_count int not null default 0,
  locked_until timestamptz,
  last_seen timestamptz,
  created_at timestamptz not null default now(),
  unique (class_id, num)
);

create table if not exists public.student_sessions (
  token text primary key,
  student_id uuid not null references public.students(id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '30 days'
);

create table if not exists public.saves (
  student_id uuid not null references public.students(id) on delete cascade,
  part text not null check (part in ('profile','free','camp-toy','camp-ch1','camp-ch2','camp-ch3','camp-ch4','camp-ch5','camp-ch6')),
  data jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (student_id, part)
);

create table if not exists public.packs (
  class_id uuid primary key references public.classes(id) on delete cascade,
  data jsonb not null,
  updated_at timestamptz not null default now()
);

create index if not exists students_class_idx on public.students(class_id);
create index if not exists sessions_student_idx on public.student_sessions(student_id);

-- ---------- 학급 코드 자동 생성 (헷갈리는 글자 0 O 1 I L 제외) ----------
create or replace function public.gen_class_code() returns text
language plpgsql volatile set search_path = public, extensions as $$
declare
  alphabet text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  c text;
begin
  loop
    c := '';
    for i in 1..6 loop
      c := c || substr(alphabet, 1 + floor(random() * length(alphabet))::int, 1);
    end loop;
    exit when not exists (select 1 from public.classes where code = c);
  end loop;
  return c;
end $$;

create or replace function public.classes_set_code() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.code is null or new.code = '' then new.code := public.gen_class_code(); end if;
  new.code := upper(new.code);
  return new;
end $$;

drop trigger if exists classes_code on public.classes;
create trigger classes_code before insert on public.classes
  for each row execute function public.classes_set_code();
alter table public.classes alter column code set default '';

-- ---------- RLS: 선생님은 자기 학급만 ----------
alter table public.classes enable row level security;
alter table public.students enable row level security;
alter table public.student_sessions enable row level security;
alter table public.saves enable row level security;
alter table public.packs enable row level security;

drop policy if exists classes_owner on public.classes;
create policy classes_owner on public.classes for all to authenticated
  using (teacher_id = auth.uid()) with check (teacher_id = auth.uid());

drop policy if exists students_owner on public.students;
create policy students_owner on public.students for all to authenticated
  using (exists (select 1 from public.classes c where c.id = class_id and c.teacher_id = auth.uid()))
  with check (exists (select 1 from public.classes c where c.id = class_id and c.teacher_id = auth.uid()));

drop policy if exists saves_owner_read on public.saves;
create policy saves_owner_read on public.saves for select to authenticated
  using (exists (select 1 from public.students s join public.classes c on c.id = s.class_id
                 where s.id = student_id and c.teacher_id = auth.uid()));

drop policy if exists packs_owner on public.packs;
create policy packs_owner on public.packs for all to authenticated
  using (exists (select 1 from public.classes c where c.id = class_id and c.teacher_id = auth.uid()))
  with check (exists (select 1 from public.classes c where c.id = class_id and c.teacher_id = auth.uid()));
-- student_sessions 에는 정책이 없음 = 함수 밖에서는 아무도 못 읽음.

-- pin_hash 는 선생님 화면에서도 읽을 필요가 없으니, 표 전체 읽기 권한을 빼고 필요한 열만 다시 줌
revoke select on public.students from anon, authenticated;
grant select (id, class_id, num, name, fail_count, locked_until, last_seen, created_at) on public.students to authenticated;
revoke all on public.student_sessions from anon, authenticated;

-- ---------- 학생용 함수 (anon 이 호출, 안에서 토큰 확인) ----------
create or replace function public._student_from_token(p_token text) returns uuid
language sql stable security definer set search_path = public as $$
  select student_id from public.student_sessions
  where token = p_token and expires_at > now()
$$;
revoke all on function public._student_from_token(text) from public, anon, authenticated;

create or replace function public.student_login(p_code text, p_num int, p_pin text) returns json
language plpgsql volatile security definer set search_path = public, extensions as $$
declare
  st public.students%rowtype;
  cl public.classes%rowtype;
  tok text;
begin
  select * into cl from public.classes where code = upper(trim(p_code));
  if not found then return json_build_object('ok', false, 'error', 'no_class'); end if;
  select * into st from public.students where class_id = cl.id and num = p_num;
  if not found then return json_build_object('ok', false, 'error', 'no_student'); end if;
  if st.locked_until is not null and st.locked_until > now() then
    return json_build_object('ok', false, 'error', 'locked', 'until', st.locked_until);
  end if;
  if st.pin_hash <> crypt(coalesce(p_pin, ''), st.pin_hash) then
    update public.students
       set fail_count = fail_count + 1,
           locked_until = case when fail_count + 1 >= 5 then now() + interval '5 minutes' else null end
     where id = st.id;
    return json_build_object('ok', false, 'error', 'bad_pin');
  end if;
  update public.students set fail_count = 0, locked_until = null, last_seen = now() where id = st.id;
  delete from public.student_sessions where student_id = st.id and expires_at < now();
  tok := encode(gen_random_bytes(24), 'hex');
  insert into public.student_sessions(token, student_id) values (tok, st.id);
  return json_build_object('ok', true, 'token', tok,
    'student', json_build_object('id', st.id, 'num', st.num, 'name', st.name),
    'class', json_build_object('name', cl.name, 'code', cl.code));
end $$;

create or replace function public.student_load(p_token text) returns json
language plpgsql stable security definer set search_path = public as $$
declare sid uuid; cid uuid;
begin
  sid := public._student_from_token(p_token);
  if sid is null then return json_build_object('ok', false, 'error', 'bad_token'); end if;
  select class_id into cid from public.students where id = sid;
  return json_build_object('ok', true,
    'parts', coalesce((select json_object_agg(part, data) from public.saves where student_id = sid), '{}'::json),
    'stamps', coalesce((select json_object_agg(part, updated_at) from public.saves where student_id = sid), '{}'::json),
    'pack', (select data from public.packs where class_id = cid));
end $$;

create or replace function public.student_save(p_token text, p_part text, p_data jsonb) returns json
language plpgsql volatile security definer set search_path = public as $$
declare sid uuid;
begin
  sid := public._student_from_token(p_token);
  if sid is null then return json_build_object('ok', false, 'error', 'bad_token'); end if;
  if p_part not in ('profile','free','camp-toy','camp-ch1','camp-ch2','camp-ch3','camp-ch4','camp-ch5','camp-ch6') then
    return json_build_object('ok', false, 'error', 'bad_part');
  end if;
  if pg_column_size(p_data) > 1500000 then return json_build_object('ok', false, 'error', 'too_large'); end if;
  insert into public.saves(student_id, part, data, updated_at) values (sid, p_part, p_data, now())
    on conflict (student_id, part) do update set data = excluded.data, updated_at = now();
  update public.students set last_seen = now() where id = sid;
  return json_build_object('ok', true, 'at', now());
end $$;

create or replace function public.student_logout(p_token text) returns json
language sql volatile security definer set search_path = public as $$
  delete from public.student_sessions where token = p_token;
  select json_build_object('ok', true);
$$;

-- ---------- 선생님용 함수 (authenticated, 자기 학급인지 안에서 확인) ----------
-- 학생 여러 명 추가. p_rows = [{"num":1,"name":"김하윤"}, ...]. 비밀번호(4자리)를 새로 만들어 한 번만 돌려줌.
create or replace function public.teacher_add_students(p_class uuid, p_rows jsonb) returns json
language plpgsql volatile security definer set search_path = public, extensions as $$
declare r jsonb; pin text; out jsonb := '[]'::jsonb; n int; nm text;
begin
  if not exists (select 1 from public.classes where id = p_class and teacher_id = auth.uid()) then
    raise exception 'not your class';
  end if;
  for r in select * from jsonb_array_elements(p_rows) loop
    n := (r->>'num')::int; nm := left(trim(r->>'name'), 20);
    if n is null or n < 1 or n > 99 or nm is null or nm = '' then continue; end if;
    pin := lpad((floor(random() * 10000))::int::text, 4, '0');
    insert into public.students(class_id, num, name, pin_hash)
      values (p_class, n, nm, crypt(pin, gen_salt('bf')))
      on conflict (class_id, num) do update set name = excluded.name, pin_hash = excluded.pin_hash, fail_count = 0, locked_until = null;
    out := out || jsonb_build_object('num', n, 'name', nm, 'pin', pin);
  end loop;
  return json_build_object('ok', true, 'students', out);
end $$;

create or replace function public.teacher_reset_pin(p_student uuid) returns json
language plpgsql volatile security definer set search_path = public, extensions as $$
declare pin text;
begin
  if not exists (select 1 from public.students s join public.classes c on c.id = s.class_id
                 where s.id = p_student and c.teacher_id = auth.uid()) then
    raise exception 'not your student';
  end if;
  pin := lpad((floor(random() * 10000))::int::text, 4, '0');
  update public.students set pin_hash = crypt(pin, gen_salt('bf')), fail_count = 0, locked_until = null where id = p_student;
  delete from public.student_sessions where student_id = p_student;
  return json_build_object('ok', true, 'pin', pin);
end $$;

-- ---------- 권한 ----------
revoke all on function public.student_login(text,int,text) from public;
revoke all on function public.student_load(text) from public;
revoke all on function public.student_save(text,text,jsonb) from public;
revoke all on function public.student_logout(text) from public;
revoke all on function public.teacher_add_students(uuid,jsonb) from public, anon;
revoke all on function public.teacher_reset_pin(uuid) from public, anon;
revoke all on function public.gen_class_code() from public, anon, authenticated;
revoke all on function public.classes_set_code() from public, anon, authenticated;
grant execute on function public.student_login(text,int,text) to anon, authenticated;
grant execute on function public.student_load(text) to anon, authenticated;
grant execute on function public.student_save(text,text,jsonb) to anon, authenticated;
grant execute on function public.student_logout(text) to anon, authenticated;
grant execute on function public.teacher_add_students(uuid,jsonb) to authenticated;
grant execute on function public.teacher_reset_pin(uuid) to authenticated;
