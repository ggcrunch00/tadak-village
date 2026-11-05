# 학급 로그인 (class-login) 설정

여러 게임이 같이 쓰는 학급 로그인이에요.
- **선생님(누구나):** Google 계정으로 로그인 → 학급 만들기 → 학생 번호 추가 → 그림 비밀번호 카드 인쇄 → 게임 기록 보기, 글감 보내기
- **학생:** 게임 첫 화면에서 **학급 코드(5글자) + 번호 + 그림 비밀번호(동물 1 + 과일 1)**
- **학생 이름은 수집하지 않아요.** 서버에는 학급 이름, 번호, 그림 비밀번호, 게임 기록만 있어요. 선생님이 관리 화면에 적는 이름은 그 컴퓨터의 브라우저에만 저장돼요.

관리 사이트(임시 주소): https://ggcrunch00.github.io/tadak-village/class-login/

## 1. Supabase (서버)
1. supabase.com 로그인 → 프로젝트 하나(이름 예: 우리 반 앱 서버, 지역 Seoul).
2. **SQL Editor** → `supabase/schema.sql` 전체를 붙여 넣고 **Run**. (여러 번 실행해도 괜찮아요)
3. **Project Settings → API**에서 **Project URL**과 **anon(publishable) 공개 키**를 확인해요.
   - ⚠️ service_role / secret 키는 절대 쓰지 마세요.

## 2. Google 로그인 켜기 (한 번)
### Google Cloud
1. https://console.cloud.google.com → 새 프로젝트(이름 아무거나, 예: class-login).
2. **API 및 서비스 → OAuth 동의 화면**: 사용자 유형 **외부**, 앱 이름(예: 학급 로그인), 지원 이메일 입력. 범위는 기본(email, profile)만.
   - 누구나 로그인하게 하려면 동의 화면을 **게시(프로덕션)** 상태로 바꿔요. "테스트" 상태에서는 등록한 테스트 사용자만 로그인돼요.
   - 기본 범위(이메일, 프로필)만 쓰면 보통 Google 검토가 필요 없다고 안내돼 있지만, 화면에 검토 요청이 나오면 그 안내를 따라 주세요.
3. **사용자 인증 정보 → 사용자 인증 정보 만들기 → OAuth 클라이언트 ID**: 유형 **웹 애플리케이션**
   - 승인된 JavaScript 원본: `https://ggcrunch00.github.io`
   - 승인된 리디렉션 URI: `https://<내 프로젝트>.supabase.co/auth/v1/callback` (Supabase 의 Google 설정 화면에 정확한 주소가 나와요)
   - 만들면 **클라이언트 ID**와 **클라이언트 보안 비밀번호**가 나와요.

### Supabase
4. **Authentication → Sign In / Providers → Google**: 켜고, 위의 클라이언트 ID와 보안 비밀번호를 붙여 넣고 저장.
   - 클라이언트 보안 비밀번호는 Supabase 에만 넣어요. 저장소나 채팅에 올리지 마세요.
5. **Authentication → URL Configuration**
   - Site URL: `https://ggcrunch00.github.io/tadak-village/class-login/`
   - Redirect URLs 에 추가: `https://ggcrunch00.github.io/**`

(메뉴 이름은 Google 과 Supabase 화면이 바뀌면 조금 다를 수 있어요.)

## 3. 게임과 관리 사이트에 연결
`tadak-village` 저장소 맨 위에 `server.json` 을 만들어요(GitHub → Add file → Create new file):
```json
{ "url": "https://<내 프로젝트>.supabase.co", "key": "anon 공개 키" }
```
커밋하면 1~2분 뒤 게임과 관리 사이트가 다시 배포돼요. 게임 첫 화면에 "학급으로 로그인"이 생기고, 관리 사이트에서 Google 로그인이 돼요.

## 4. 수업에서
1. 관리 사이트 → Google 로그인 → **새 학급** → 학급 코드(5글자)가 나와요.
2. "1번부터 25번까지 추가" → 번호마다 그림 비밀번호가 무작위로 정해져요. (원하면 "그림 바꾸기")
3. 이름 칸은 선택. 적으면 이 컴퓨터에서만 보여요.
4. **로그인 카드 인쇄** → 잘라서 나눠 줘요(학급 코드, 번호, 그림 두 개, 게임 주소).
5. 학생은 게임 첫 화면 → 학급 코드, 번호 → 동물 하나, 과일 하나 → 로그인.

## 보안과 한계 (일부러 단순하게)
- 그림 비밀번호는 64가지예요. 대신 5번 틀리면 5분 잠기고, 선생님이 언제든 바꿀 수 있어요.
- 선생님은 자기 학급만 보고 고칠 수 있어요. 로그인하지 않은 사람은 표를 직접 읽지 못하고, 학생은 토큰을 받는 함수로만 자기 기록을 읽고 써요. (로컬 PostgreSQL 16 으로 시험)
- 그림 비밀번호는 선생님이 카드를 다시 뽑을 수 있도록 선생님만 볼 수 있는 칸에 그대로 저장해요.
- 무료 요금제는 7일쯤 조용하면 일시 정지될 수 있어요. `tadak-village` 의 keepalive 작업이 3일마다 깨워요(확실히 막는다는 보장은 없어요).
- 학교에서 쓸 때는 학교의 학습지원 소프트웨어 선정 절차(학교운영위원회 심의 등)를 확인해 주세요. 이름을 받지 않으므로 수집 항목은 학급 이름, 번호, 게임 기록이에요.

## 다른 게임에 붙이기
```html
<script src="https://ggcrunch00.github.io/tadak-village/class-login/classlogin.js"></script>
<script>
  ClassLogin.init({ url, key, app: 'my-game' });          // app: 영문 소문자, 게임마다 다르게
  ClassLogin.mountStudentLogin(el, { onLogin(s){ /* s.student.num, s.cls.name */ } });
  await ClassLogin.save('progress', {...});               // 게임 저장 (부분마다 1.5MB, 30개까지)
  const r = await ClassLogin.load();                     // r.parts.progress, r.pack (선생님 글감)
  await ClassLogin.save('summary', {title:'내 게임', cols:['점수'], fields:{'점수': 12}, proposals:[]});
  //  └ summary 는 관리 사이트 "게임 기록" 표에 그대로 보여요
</script>
```
관리 사이트의 게임 목록은 `server.json` 의 `games` 에 추가해요: `{"app":"my-game","title":"내 게임","url":"https://..."}`
