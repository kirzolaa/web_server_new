import instaloader
import pandas as pd
import time
import json
import tkinter as tk
from tkinter import ttk

# Initialize Instaloader
loader = instaloader.Instaloader()

# List of usernames to fetch data for
usernames = [
    "alice_nguyen_sunshine", "Emicheer3", "alexafitness0",
    "mariatravel1990", "dorapinup83", "fernandobailando1",
    "isabellaotaku23", "inem.esis", "latifaadventures"
]

# Excel file name
excel_file = "Instagram_Profile_Data.xlsx"
json_file = "Instagram_Profile_Data.json"

# Initialize a dictionary to store data
all_data = {}

# Calculate the total steps based on media counts
media_counts = []
total_steps = 36  # Start with 36 steps for the profile and post info

# Create the Tkinter window for progress
window = tk.Tk()
window.title("Progress Window")
window.geometry("400x200")  # Fixed size for the window
window.resizable(False, False)  # Disable resizing

# Progress bar setup
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(window, variable=progress_var, maximum=100, length=300)
progress_bar.pack(pady=30)

# Progress label
progress_label = tk.Label(window, text="Progress: Initializing...", font=('Arial', 12))
progress_label.pack()

# Elapsed time label
elapsed_time_label = tk.Label(window, text="Elapsed Time: 0.00 seconds", font=('Arial', 10))
elapsed_time_label.pack()

# Force the window to display immediately
window.update()

# Store the start time
start_time = time.time()

# Function to update the progress bar and labels
def update_progress(current_step):
    elapsed_time = time.time() - start_time
    percent = (current_step / total_steps) * 100

    progress_var.set(percent)
    progress_label.config(text=f"Progress: {current_step}/{total_steps} ({percent:.2f}%)")
    elapsed_time_label.config(text=f"Elapsed Time: {elapsed_time:.2f} seconds")
    window.update()

# Fetching media counts for progress calculation
for username in usernames:
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        media_counts.append(profile.mediacount)
        time.sleep(5)
    except Exception as e:
        print(f"Error fetching data for {username}: {e}")
total_steps += sum(media_counts)  # Add media count from each user

# Begin fetching Instagram data and saving it
current_step = 0
try:
    # Open Excel writer
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:

        for username in usernames:
            try:
                print(f"\nFetching data for {username}...")
                update_progress(current_step)

                # Fetch profile data
                profile = instaloader.Profile.from_username(loader.context, username)

                # --- Worksheet 1: Profile Information ---
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
                    "Profile Picture URL": profile.profile_pic_url
                }

                # Add to all_data dictionary
                all_data[username] = {
                    "profile": profile_data,
                    "posts": []
                }

                # Save profile data to a worksheet
                profile_df = pd.DataFrame([profile_data])
                profile_df.to_excel(writer, sheet_name=f"{username}_Profile", index=False)

                # --- Worksheet 2: Post Details ---
                post_data = []
                for post in profile.get_posts():
                    post_info = {
                        "Post Date": post.date_utc,
                        "Caption": post.caption,
                        "Likes": post.likes,
                        "Comments": post.comments,
                        "Is Video": post.is_video,
                        "Video Duration": post.video_duration if post.is_video else None,
                        "Post URL": post.url
                    }
                    post_data.append(post_info)

                    # Add to the all_data dictionary
                    all_data[username]["posts"].append(post_info)

                    # Update progress and sleep between requests
                    current_step += 1
                    update_progress(current_step)
                    time.sleep(5)

                # Save post data to a worksheet
                post_df = pd.DataFrame(post_data)
                post_df.to_excel(writer, sheet_name=f"{username}_Posts", index=False)

                print(f"Data for {username} saved successfully!")

                # Sleep between users
                time.sleep(10)

            except Exception as e:
                print(f"Error fetching data for {username}: {e}")

    print(f"All data has been written to {excel_file}.")
    update_progress(total_steps)

    # Save all data to JSON file
    with open(json_file, 'w') as jsonf:
        json.dump(all_data, jsonf, indent=4)

    print(f"All data has been written to {json_file}.")

except Exception as e:
    print(f"Error saving files: {e}")

# Mark completion
progress_label.config(text="Processing Complete!")
elapsed_time_label.config(text=f"Total Time: {time.time() - start_time:.2f} seconds")

# Start the Tkinter event loop
window.mainloop()
