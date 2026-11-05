-- 예전 v1 설정(이름을 쓰는 섬 전용, 숫자 비밀번호)의 표와 함수를 지워요.
-- 표에 데이터가 있으면 아무것도 지우지 않고 멈춰요.
do $$
declare n int := 0;
begin
  if to_regclass('public.students') is not null then execute 'select count(*) from public.students' into n; end if;
  if n > 0 then raise exception '예전 students 표에 % 명이 있어요. 지우지 않았어요.', n; end if;
end $$;

drop function if exists public.student_login(text,int,text);
drop function if exists public.student_load(text);
drop function if exists public.student_save(text,text,jsonb);
drop function if exists public.student_logout(text);
drop function if exists public.teacher_add_students(uuid,jsonb);
drop function if exists public.teacher_reset_pin(uuid);
drop function if exists public._student_from_token(text);
drop table if exists public.packs, public.saves, public.student_sessions, public.students, public.classes;
drop function if exists public.classes_set_code();
drop function if exists public.gen_class_code();
