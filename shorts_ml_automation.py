import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import pandas as pd
import os
import threading
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

class ShortsCommentMLGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎥 YouTube Shorts 댓글 ML 자동화")
        self.root.geometry("700x500")
        self.root.configure(bg="#f0f0f0")

        tk.Label(self.root, text="YouTube Shorts 댓글 크롤링 + ML 분석", font=("맑은 고딕", 16, "bold"), bg="#f0f0f0").pack(pady=10)

        tk.Label(self.root, text="1. Shorts URL:", bg="#f0f0f0").pack(anchor="w", padx=20)
        self.url_entry = tk.Entry(self.root, width=80)
        self.url_entry.insert(0, "https://www.youtube.com/shorts/UkU_P-jfBtM")
        self.url_entry.pack(padx=20, pady=5)

        tk.Label(self.root, text="2. 크롤링 건수:", bg="#f0f0f0").pack(anchor="w", padx=20)
        self.cnt_entry = tk.Entry(self.root, width=20)
        self.cnt_entry.insert(0, "50")
        self.cnt_entry.pack(padx=20, pady=5)

        tk.Label(self.root, text="3. 저장 폴더:", bg="#f0f0f0").pack(anchor="w", padx=20)
        self.folder_var = tk.StringVar(value="c:\\py_temp\\쇼츠댓글ML")
        tk.Entry(self.root, textvariable=self.folder_var, width=80).pack(padx=20, pady=5)

        self.start_btn = tk.Button(self.root, text="🚀 크롤링 + ML 분석 시작", font=("맑은 고딕", 12, "bold"),
                                   bg="#4CAF50", fg="white", height=2, command=self.start_thread)
        self.start_btn.pack(pady=20)

        self.status = tk.Label(self.root, text="대기 중... 버튼을 눌러주세요", fg="blue", font=("맑은 고딕", 10))
        self.status.pack(pady=10)

        self.root.mainloop()

    def start_thread(self):
        threading.Thread(target=self.run_all, daemon=True).start()

    def run_all(self):
        try:
            self.start_btn.config(state="disabled")
            self.status.config(text="브라우저 실행 중...", fg="orange")

            url = self.url_entry.get().strip()
            cnt = int(self.cnt_entry.get())
            f_dir = self.folder_var.get()
            os.makedirs(f_dir, exist_ok=True)

            s = Service("c:/py_temp/chromedriver.exe")   # ← 여기 본인 경로로 바꾸세요!
            driver = webdriver.Chrome(service=s)
            driver.get(url)
            driver.maximize_window()
            time.sleep(5)

            try:
                driver.find_element(By.XPATH, '//*[@id="button-bar"]/reel-action-bar-view-model/button-view-model[1]').click()
                time.sleep(3)
            except:
                pass

            count = 0
            prev_count = 0
            data = {'동영상 URL': [], '댓글작성자명': [], '댓글 작성일자': [], '리뷰내용': [], '좋아요횟수': []}

            while count < cnt:
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                comments = soup.find_all('ytd-comment-thread-renderer')

                for li in comments:
                    if count >= cnt: break
                    try:
                        reviewer = li.find('a', class_='yt-simple-endpoint style-scope ytd-comment-view-model').get_text(strip=True)
                        date = li.find('span', id='published-time-text').get_text(strip=True)
                        content = li.find('span', class_='yt-core-attributed-string--white-space-pre-wrap').get_text(strip=True)
                        like_node = li.select_one('like-button-view-model span[role="text"]') or li.select_one('#vote-count-middle')
                        like = like_node.get_text(strip=True) if like_node else '0'

                        data['동영상 URL'].append(url)
                        data['댓글작성자명'].append(reviewer)
                        data['댓글 작성일자'].append(date)
                        data['리뷰내용'].append(content)
                        data['좋아요횟수'].append(like)
                        count += 1
                    except:
                        continue

                if count == prev_count: break
                prev_count = count

            driver.quit()

            df = pd.DataFrame(data)
            df['리뷰길이'] = df['리뷰내용'].str.len()
            df['좋아요횟수'] = pd.to_numeric(df['좋아요횟수'], errors='coerce').fillna(0)

            if len(df) > 10:
                X = df[['리뷰길이']]
                y = df['좋아요횟수']
                model = LinearRegression()
                model.fit(X, y)
                df['예측좋아요'] = model.predict(X).round(1)

            def sentiment(text):
                if any(w in text for w in ['좋아요','최고','대박','감사']): return '긍정'
                if any(w in text for w in ['별로','싫어','최악']): return '부정'
                return '중립'
            df['감성'] = df['리뷰내용'].apply(sentiment)

            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            csv_path = os.path.join(f_dir, f"쇼츠댓글_{timestamp}.csv")
            df.to_csv(csv_path, encoding='utf-8-sig', index=False)
            df.to_excel(csv_path.replace('.csv','.xlsx'), index=False)

            self.status.config(text=f"✅ 완료! {len(df)}건 수집 + ML 분석 끝", fg="green")
            messagebox.showinfo("성공!", f"파일 저장 완료!\n{csv_path}")

        except Exception as e:
            messagebox.showerror("오류", str(e))
        finally:
            self.start_btn.config(state="normal")

if __name__ == "__main__":
    ShortsCommentMLGUI()