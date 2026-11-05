-- 학급 로그인 (class-login) 공용 서버 설정
-- Supabase 대시보드 → SQL Editor 에 이 파일 전체를 붙여 넣고 Run. 여러 번 실행해도 괜찮아요.
--
-- 누가 무엇을
--   선생님(누구나): Google 로그인. 승인 없이 학급을 만들고, 자기 학급만 보고 고침 (RLS).
--   학생: 이메일·이름 없음. 학급 코드(5글자) + 번호 + 그림 비밀번호(동물 1 + 과일 1) → cl_student_login() 이 토큰을 줌.
--         학생은 표를 직접 읽지 못하고 토큰을 받는 함수로만 자기 저장을 읽고 씀.
--   여러 게임: 저장(cl_saves)과 글감(cl_packs)은 게임 이름(app)으로 나뉨. 학급과 학생은 모든 게임이 같이 씀.
--   개인정보: 학생 이름을 저장하는 칸이 없음. 번호와 학급 이름(선생님이 정함)만 있음.
--
-- 그림 비밀번호는 'a0'~'a7'(동물) 과 'f0'~'f7'(과일)을 이은 'a3-f5' 같은 글자예요(64가지).
-- 아이들이 쉽게 기억하도록 일부러 짧게 했고, 대신 5번 틀리면 5분 잠겨요.
-- 선생님이 언제든 카드를 다시 인쇄할 수 있도록 비밀번호는 선생님만 읽을 수 있는 칸에 그대로 둬요.

create extension if not exists pgcrypto with schema extensions;

-- ---------- 표 ----------
create table if not exists public.cl_classes (
  id uuid primary key default gen_random_uuid(),
  owner uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 40),
  code text not null unique default '',
  created_at timestamptz not null default now()
);

create table if not exists public.cl_students (
  id uuid primary key default gen_random_uuid(),
  class_id uuid not null references public.cl_classes(id) on delete cascade,
  num int not null check (num between 1 and 99),
  secret text not null check (secret ~ '^a[0-7]-f[0-7]$'),
  fail_count int not null default 0,
  locked_until timestamptz,
  last_seen timestamptz,
  created_at timestamptz not null default now(),
  unique (class_id, num)
);

create table if not exists public.cl_sessions (
  token text primary key,
  student_id uuid not null references public.cl_students(id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '30 days'
);

create table if not exists public.cl_saves (
  student_id uuid not null references public.cl_students(id) on delete cascade,
  app text not null check (app ~ '^[a-z0-9-]{2,30}$'),
  part text not null check (part ~ '^[a-z0-9_-]{1,40}$'),
  data jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (student_id, app, part)
);

create table if not exists public.cl_packs (
  class_id uuid not null references public.cl_classes(id) on delete cascade,
  app text not null check (app ~ '^[a-z0-9-]{2,30}$'),
  data jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (class_id, app)
);

create index if not exists cl_students_class_idx on public.cl_students(class_id);
create index if not exists cl_sessions_student_idx on public.cl_sessions(student_id);

-- ---------- 학급 코드: 5글자, 헷갈리는 0 O 1 I L 제외 ----------
create or replace function public.cl_gen_code() returns text
language plpgsql volatile security definer set search_path = public as $$
declare a text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; c text;
begin
  loop
    c := '';
    for i in 1..5 loop c := c || substr(a, 1 + floor(random() * length(a))::int, 1); end loop;
    exit when not exists (select 1 from public.cl_classes where code = c);
  end loop;
  return c;
end $$;

create or replace function public.cl_classes_code() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.code is null or new.code = '' then new.code := public.cl_gen_code(); end if;
  new.code := upper(new.code);
  return new;
end $$;
drop trigger if exists cl_classes_code on public.cl_classes;
create trigger cl_classes_code before insert on public.cl_classes for each row execute function public.cl_classes_code();

create or replace function public.cl_rand_secret() returns text
language sql volatile as $$ select 'a' || floor(random()*8)::int || '-f' || floor(random()*8)::int $$;

-- ---------- RLS ----------
alter table public.cl_classes enable row level security;
alter table public.cl_students enable row level security;
alter table public.cl_sessions enable row level security;
alter table public.cl_saves enable row level security;
alter table public.cl_packs enable row level security;

drop policy if exists cl_classes_owner on public.cl_classes;
create policy cl_classes_owner on public.cl_classes for all to authenticated
  using (owner = auth.uid()) with check (owner = auth.uid());

drop policy if exists cl_students_owner on public.cl_students;
create policy cl_students_owner on public.cl_students for all to authenticated
  using (exists (select 1 from public.cl_classes c where c.id = class_id and c.owner = auth.uid()))
  with check (exists (select 1 from public.cl_classes c where c.id = class_id and c.owner = auth.uid()));

drop policy if exists cl_saves_owner_read on public.cl_saves;
create policy cl_saves_owner_read on public.cl_saves for select to authenticated
  using (exists (select 1 from public.cl_students s join public.cl_classes c on c.id = s.class_id
                 where s.id = student_id and c.owner = auth.uid()));

drop policy if exists cl_packs_owner on public.cl_packs;
create policy cl_packs_owner on public.cl_packs for all to authenticated
  using (exists (select 1 from public.cl_classes c where c.id = class_id and c.owner = auth.uid()))
  with check (exists (select 1 from public.cl_classes c where c.id = class_id and c.owner = auth.uid()));

revoke all on public.cl_sessions from anon, authenticated;
revoke all on public.cl_classes, public.cl_students, public.cl_saves, public.cl_packs from anon;

-- ---------- 학생 함수 (anon 이 부름, 안에서 토큰 확인) ----------
create or replace function public._cl_sid(p_token text) returns uuid
language sql stable security definer set search_path = public as $$
  select student_id from public.cl_sessions where token = p_token and expires_at > now()
$$;
revoke all on function public._cl_sid(text) from public, anon, authenticated;

create or replace function public.cl_student_login(p_code text, p_num int, p_secret text) returns json
language plpgsql volatile security definer set search_path = public, extensions as $$
declare st public.cl_students%rowtype; cl public.cl_classes%rowtype; tok text;
begin
  select * into cl from public.cl_classes where code = upper(trim(coalesce(p_code, '')));
  if not found then return json_build_object('ok', false, 'error', 'no_class'); end if;
  select * into st from public.cl_students where class_id = cl.id and num = p_num;
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

create or replace function public.cl_student_load(p_token text, p_app text) returns json
language plpgsql stable security definer set search_path = public as $$
declare sid uuid; cid uuid;
begin
  sid := public._cl_sid(p_token);
  if sid is null then return json_build_object('ok', false, 'error', 'bad_token'); end if;
  select class_id into cid from public.cl_students where id = sid;
  return json_build_object('ok', true,
    'parts', coalesce((select json_object_agg(part, data) from public.cl_saves where student_id = sid and app = p_app), '{}'::json),
    'stamps', coalesce((select json_object_agg(part, updated_at) from public.cl_saves where student_id = sid and app = p_app), '{}'::json),
    'pack', (select data from public.cl_packs where class_id = cid and app = p_app));
end $$;

create or replace function public.cl_student_save(p_token text, p_app text, p_part text, p_data jsonb) returns json
language plpgsql volatile security definer set search_path = public as $$
declare sid uuid;
begin
  sid := public._cl_sid(p_token);
  if sid is null then return json_build_object('ok', false, 'error', 'bad_token'); end if;
  if p_app !~ '^[a-z0-9-]{2,30}$' or p_part !~ '^[a-z0-9_-]{1,40}$' then return json_build_object('ok', false, 'error', 'bad_part'); end if;
  if pg_column_size(p_data) > 1500000 then return json_build_object('ok', false, 'error', 'too_large'); end if;
  if (select count(*) from public.cl_saves where student_id = sid and app = p_app) >= 30
     and not exists (select 1 from public.cl_saves where student_id = sid and app = p_app and part = p_part) then
    return json_build_object('ok', false, 'error', 'too_many_parts');
  end if;
  insert into public.cl_saves(student_id, app, part, data, updated_at) values (sid, p_app, p_part, p_data, now())
    on conflict (student_id, app, part) do update set data = excluded.data, updated_at = now();
  update public.cl_students set last_seen = now() where id = sid;
  return json_build_object('ok', true, 'at', now());
end $$;

create or replace function public.cl_student_logout(p_token text) returns json
language sql volatile security definer set search_path = public as $$
  delete from public.cl_sessions where token = p_token;
  select json_build_object('ok', true);
$$;

-- ---------- 선생님 함수 ----------
-- 번호 여러 개를 한꺼번에 추가. 이미 있는 번호는 건너뜀. 그림 비밀번호는 무작위.
create or replace function public.cl_add_students(p_class uuid, p_nums int[]) returns json
language plpgsql volatile security definer set search_path = public as $$
declare n int;
begin
  if not exists (select 1 from public.cl_classes where id = p_class and owner = auth.uid()) then raise exception 'not your class'; end if;
  foreach n in array p_nums loop
    if n between 1 and 99 then
      insert into public.cl_students(class_id, num, secret) values (p_class, n, public.cl_rand_secret())
        on conflict (class_id, num) do nothing;
    end if;
  end loop;
  return json_build_object('ok', true);
end $$;

-- 비밀번호 바꾸기(새로 무작위, 또는 선생님이 고른 것). 잠김도 풀고 이전 로그인은 끊음.
create or replace function public.cl_set_secret(p_student uuid, p_secret text default null) returns json
language plpgsql volatile security definer set search_path = public as $$
declare s text := coalesce(p_secret, public.cl_rand_secret());
begin
  if not exists (select 1 from public.cl_students st join public.cl_classes c on c.id = st.class_id
                 where st.id = p_student and c.owner = auth.uid()) then raise exception 'not your student'; end if;
  if s !~ '^a[0-7]-f[0-7]$' then raise exception 'bad secret'; end if;
  update public.cl_students set secret = s, fail_count = 0, locked_until = null where id = p_student;
  delete from public.cl_sessions where student_id = p_student;
  return json_build_object('ok', true, 'secret', s);
end $$;

-- ---------- 함수 권한 ----------
revoke all on function public.cl_student_login(text,int,text) from public;
revoke all on function public.cl_student_load(text,text) from public;
revoke all on function public.cl_student_save(text,text,text,jsonb) from public;
revoke all on function public.cl_student_logout(text) from public;
revoke all on function public.cl_add_students(uuid,int[]) from public, anon;
revoke all on function public.cl_set_secret(uuid,text) from public, anon;
revoke all on function public.cl_gen_code() from public, anon, authenticated;
revoke all on function public.cl_classes_code() from public, anon, authenticated;
grant execute on function public.cl_student_login(text,int,text) to anon, authenticated;
grant execute on function public.cl_student_load(text,text) to anon, authenticated;
grant execute on function public.cl_student_save(text,text,text,jsonb) to anon, authenticated;
grant execute on function public.cl_student_logout(text) to anon, authenticated;
grant execute on function public.cl_add_students(uuid,int[]) to authenticated;
grant execute on function public.cl_set_secret(uuid,text) to authenticated;
