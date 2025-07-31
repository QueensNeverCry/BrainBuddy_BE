import pymysql
import csv, os

Connect = pymysql.connect(
    host="localhost",
    user="root",
    password="dnddltkfkd@050312",
    database="TestBB",
    charset="utf8mb4"
)
Session = Connect.cursor()

Directory = "/Users/v/SUN_RAT/I_AM_SEXY_QUEEN/BrainBuddy_BE/Test"

UserPW = "THIS_USER_IS_DUMMY_USER"


if __name__ == "__main__":
    filename = input("Enter FileName : ")
    filepath = os.path.join(Directory, filename)

    # CSV 파일 읽기
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_name = row["user_name"]
            total_score = float(row["total_score"])
            avg_score = float(row["avg_score"])
            total_cnt = int(row["total_cnt"])
            # created_at은 MySQL의 NOW() 함수 사용
            sql = """
                INSERT INTO TotalScore (user_name, total_score, avg_score, total_cnt)
                VALUES (%s, %s, %s, %s)
            """
            try:
                Session.execute(sql, (user_name, total_score, avg_score, total_cnt))
            except Exception as e:
                print(f"[ERROR] : Insert error for {user_name}: {e}")

    Connect.commit()
    Session.close()
    Connect.close()

    print("CSV 데이터가 MySQL에 성공적으로 입력되었습니다.")