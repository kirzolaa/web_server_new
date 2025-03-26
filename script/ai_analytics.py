# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 16:45:25 2025

@author: Zoli
"""
import instaloader
import pandas as pd
import time
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QProgressBar, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer


# Worker thread for handling data fetching in the background
class DataFetchThread(QThread):
    progress_update = pyqtSignal(int, str)
    total_steps_update = pyqtSignal(int)
    finished = pyqtSignal(float)
    error_signal = pyqtSignal(str)

    def __init__(self, usernames, loader, excel_file, json_file):
        super().__init__()
        self.usernames = usernames
        self.loader = loader
        self.excel_file = excel_file
        self.json_file = json_file

    def run(self):
        total_steps = 36  # Start with 36 steps for profiles
        all_data = {}
        media_counts = []

        # Calculate total steps
        try:
            for username in self.usernames:
                try:
                    profile = instaloader.Profile.from_username(self.loader.context, username)
                    media_counts.append(profile.mediacount)
                    time.sleep(3)  # Delay to prevent API throttling
                except Exception as e:
                    self.error_signal.emit(f"Error fetching media count for {username}: {e}")
            total_steps += sum(media_counts)
            self.total_steps_update.emit(total_steps)
        except Exception as e:
            self.error_signal.emit(f"Error during media count fetching: {e}")
            return

        # Begin fetching data
        current_step = 0
        start_time = time.time()
        try:
            with pd.ExcelWriter(self.excel_file, engine="openpyxl") as writer:
                for username in self.usernames:
                    try:
                        profile = instaloader.Profile.from_username(self.loader.context, username)
                        profile_data = {
                            "Username": profile.username,
                            "Full Name": profile.full_name,
                            "Biography": profile.biography,
                            "Followers": profile.followers,
                            "Following": profile.followees,
                            "Media Count": profile.mediacount,
                            "Is Private": profile.is_private,
                            "Is Verified": profile.is_verified,
                            "External URL": profile.external_url,
                            "Business Category": profile.business_category_name,
                            "Profile Picture URL": profile.profile_pic_url,
                        }

                        all_data[username] = {"profile": profile_data, "posts": []}
                        profile_df = pd.DataFrame([profile_data])
                        profile_df.to_excel(writer, sheet_name=f"{username}_Profile", index=False)

                        post_data = []
                        for post in profile.get_posts():
                            post_info = {
                                "Post Date": post.date_utc,
                                "Caption": post.caption,
                                "Likes": post.likes,
                                "Comments": post.comments,
                                "Is Video": post.is_video,
                                "Video Duration": post.video_duration if post.is_video else None,
                                "Post URL": post.url,
                            }
                            post_data.append(post_info)
                            all_data[username]["posts"].append(post_info)

                            current_step += 1
                            self.progress_update.emit(current_step, f"Processing posts for {username}...")
                            time.sleep(3)  # Delay between post fetches

                        post_df = pd.DataFrame(post_data)
                        post_df.to_excel(writer, sheet_name=f"{username}_Posts", index=False)
                        self.progress_update.emit(current_step, f"Finished processing {username}.")

                        time.sleep(5)  # Delay between users
                    except Exception as e:
                        self.error_signal.emit(f"Error fetching data for {username}: {e}")

            # Save all data to JSON
            with open(self.json_file, "w") as jsonf:
                json.dump(all_data, jsonf, indent=4)

            self.finished.emit(time.time() - start_time)
        except Exception as e:
            self.error_signal.emit(f"Error during data saving: {e}")

# Main application window
class MainWindow(QMainWindow):
    def __init__(self, usernames, excel_file, json_file):
        super().__init__()
        self.setWindowTitle("Instagram Data Fetcher @ AI Agency")
        self.resize(600, 400)  # Set an initial size (resizable by default)

        # Initialize layout
        self.layout = QVBoxLayout()

        # Add vertical stretch before widgets (to center vertically)
        self.layout.addStretch(1)

        # Labels and progress bar
        self.progress_label = QLabel("Initializing...\nThis might take a while. Please be patient!", self)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar)

        self.elapsed_time_label = QLabel("Elapsed Time: 0.00 seconds", self)
        self.elapsed_time_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.elapsed_time_label)

        # Add vertical stretch after widgets (to center vertically)
        self.layout.addStretch(1)

        # Central widget setup
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # Initialize worker thread
        self.thread = DataFetchThread(usernames, instaloader.Instaloader(), excel_file, json_file)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.total_steps_update.connect(self.set_total_steps)
        self.thread.finished.connect(self.on_finished)
        self.thread.error_signal.connect(self.show_error)

        self.total_steps = 100
        self.start_time = time.time()

        # Timer for live elapsed time updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_elapsed_time)
        self.timer.start(1000)  # Update every 1 second

        # Start thread
        self.thread.start()

    def set_total_steps(self, total_steps):
        self.total_steps = total_steps
        self.progress_bar.setRange(0, total_steps)

    def update_progress(self, current_step, message):
        self.progress_bar.setValue(current_step)
        self.progress_label.setText(message)

    def update_elapsed_time(self):
        elapsed_time = time.time() - self.start_time
        self.elapsed_time_label.setText(f"Elapsed Time: {elapsed_time:.2f} seconds")

    def on_finished(self, elapsed_time):
        self.progress_label.setText("Processing Complete!")
        self.timer.stop()  # Stop the timer once processing is complete
        self.elapsed_time_label.setText(f"Total Time: {elapsed_time:.2f} seconds")

    def show_error(self, error_message):
        self.progress_label.setText(f"Error: {error_message}")


# Main script execution
if __name__ == "__main__":
    import sys

    usernames = [
        "alice_nguyen_sunshine", "Emicheer3", "alexafitness0", "mariatravel1990", "dorapinup83", "fernandobailando1", "isabellaotaku23", "inem.esis", "latifaadventures",
    ]
    excel_file = "Instagram_Profile_Data.xlsx"
    json_file = "Instagram_Profile_Data.json"

    app = QApplication(sys.argv)
    window = MainWindow(usernames, excel_file, json_file)
    window.show()
    sys.exit(app.exec_())
