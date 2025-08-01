import os, csv
import random

Directory = "/Users/v/SUN_RAT/I_AM_SEXY_QUEEN/BrainBuddy_BE/Test/data"

if __name__ == "__main__":
    filename = input("Enter FileName : ")
    filepath = os.path.join(Directory, filename)

    dummy_data = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dummy_data.append((row["email"], row["user_name"]))

    with open(filepath, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["email", "user_name", "total_score", "avg_score", "total_cnt"])  # 헤더

        for email, username in dummy_data:
            total_score = round(random.uniform(0, 10000), 3)
            avg_score = round(random.uniform(0, 100), 3)
            total_cnt = random.randint(0, 50)
            writer.writerow([email, username, total_score, avg_score, total_cnt])

    print(f"Added score columns to {filename}")