import random, string, re
import os, csv

Directory = "/Users/v/SUN_RAT/I_AM_SEXY_QUEEN/BrainBuddy_BE/Test/data"

NamePattern = r'^[A-Za-z0-9가-힣_-]{2,16}$'
# 모든 한글 유니코드 범위를 포함
HangulChars = ''.join([chr(i) for i in range(0xAC00, 0xD7A4)])
NameCharSet = string.ascii_letters + string.digits + HangulChars + '_-'

Surnames = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '연', '맹', '우', '전', '백']
Firstnames = ['민수', '서연', '지훈', '수빈', '현우', '지민', '현서', '유진', '시우', '은우', '기홍', '승빈', '주현', '서연', '서현', '건웅', '요한', '재명']
Adjectives = ['happy', 'blue', 'fast', 'silent', 'clever', 'brave']
Nouns = ['tiger', 'cat', 'lion', 'sky', 'coder', 'panda']

Domains = ["@gmail.com", "@naver.com", "@skku.edu"]
EmailCharSet = string.ascii_letters + string.digits + "_-"

UsedEmails = set()
UsedNames = set()

def gen_realistic_korean_name():
    name = random.choice(Surnames) + random.choice(Firstnames)
    if 2 <= len(name) <= 16:
        return name
    else:
        return gen_realistic_korean_name()

def gen_realistic_nickname():
    name = random.choice(Adjectives) + '_' + random.choice(Nouns) + str(random.randint(1, 999))
    name = name[:16]  # 길이 제한
    if re.match(NamePattern, name):
        return name
    else:
        return gen_realistic_nickname()

def gen_user_name():
    if random.random() < 0.5:
        return gen_realistic_korean_name()
    else:
        return gen_realistic_nickname()

def gen_email() -> str:
    while True:
        domain = random.choice(Domains)
        local_len = random.randint(5, 32 - len(domain))
        local_part = ''.join(random.choices(EmailCharSet, k=local_len))
        email = local_part + domain
        if len(email) <= 32 and email not in UsedEmails:
            UsedEmails.add(email)
            return email
        
if __name__ == "__main__":
    N = int(input("Enter the number of dummy users to generate: "))

    dummy_data = []

    while len(dummy_data) < N:
        username = gen_user_name()
        if username in UsedNames:
            continue  # 닉네임 중복이면 다시 시도
        UsedNames.add(username)
        email = gen_email()
        dummy_data.append((email, username))

    print(f"[DEBUG] :: len(dummy_data) dummy user(s) created.")
    
    filename = f"{len(dummy_data)}_dummy_users.csv"
    filepath = os.path.join(Directory, filename)
    with open(filepath, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["email", "user_name"])
        for email, username in dummy_data:
            writer.writerow([email, username])

    print(f"[FINISH] :: {filename} has created.")