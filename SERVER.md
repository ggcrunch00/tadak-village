# 학급 서버

이 게임은 공용 **학급 로그인(class-login)** 을 써요. 설정 방법은 [class-login/SETUP.md](class-login/SETUP.md) 에 있어요.

- 선생님: Google 로그인 → 관리 사이트(https://ggcrunch00.github.io/tadak-village/class-login/)에서 학급, 학생 번호, 그림 비밀번호, 기록, 글감
- 학생: 학급 코드 + 번호 + 그림 비밀번호(동물 1 + 과일 1)
- 학생 이름은 서버로 보내지 않아요.
- 서버가 없거나 닿지 않으면 게임은 "이 컴퓨터에 저장"으로 계속 동작해요.

예전 v1 설정(`classes`, `students` 표와 숫자 비밀번호)은 더 이상 쓰지 않아요. 이미 실행했다면 `class-login/supabase/cleanup_v1.sql` 로 지울 수 있어요(표가 비어 있을 때만).
