import functools
import datetime
import time
import csv
import re
import os
from . import write
NEWLINE = '\n'
ISOFORMAT = datetime.datetime.isoformat
NOW    = datetime.datetime.now
def store_already_written_videos(file_name, file_type):
 with open(f'{file_name}.{file_type}', 'r', encoding='utf-8') as file:
  if file_type == 'txt' or file_type == 'md': return set(re.findall('(https://www\.youtube\.com/watch\?v=.+?)(?:\s|\n)', file.read()))
  if file_type == 'csv':       return set(re.findall('(https://www\.youtube\.com/watch\?v=.+?),', file.read()))
def scroll_down(driver, scroll_pause_time, logging_output_location):
 driver.execute_script('window.scrollBy(0, 50000);')
 time.sleep(scroll_pause_time * 2)
 new_elements_count = driver.execute_script('return document.querySelectorAll("ytd-grid-video-renderer").length')
 logging_output_location.writelines(f'{ISOFORMAT(NOW())}: Found {new_elements_count} videos...{NEWLINE}')
 if driver.find_elements_by_xpath('//*[@id="video-title"]')[-1].get_attribute("href") in VISITED_VIDEOS:
  return True
 return False
def save_elements_to_list(driver, start_time, scroll_pause_time, url, logging_output_location):
 elements = driver.find_elements_by_xpath('//*[@id="video-title"]')
 end_time = time.perf_counter()
 total_time = end_time - start_time - scroll_pause_time
 logging_output_location.writelines(f'{ISOFORMAT(NOW())}: It took {total_time} seconds to find {len(elements)} videos from {url}{NEWLINE}{NEWLINE}')
 return elements
def scroll_to_old_videos(url, driver, scroll_pause_time, txt_exists, csv_exists, md_exists, file_name, logging_output_location):
 global VISITED_VIDEOS, STORED_IN_TXT, STORED_IN_CSV, STORED_IN_MD
 STORED_IN_TXT = set()
 STORED_IN_CSV = set()
 STORED_IN_MD  = set()
 if txt_exists: STORED_IN_TXT = store_already_written_videos(file_name, 'txt')
 if csv_exists: STORED_IN_CSV = store_already_written_videos(file_name, 'csv')
 if md_exists:  STORED_IN_MD =  store_already_written_videos(file_name, 'md' )
 VISITED_VIDEOS = STORED_IN_TXT.intersection(STORED_IN_CSV).intersection(STORED_IN_MD)
 logging_output_location.writelines(f'{ISOFORMAT(NOW())}: Detected an existing file with the name {file_name} in this directory, checking for new videos to update {file_name}....{NEWLINE}')
 start_time    = time.perf_counter()
 found_old_videos = False
 while found_old_videos is False:
  found_old_videos = scroll_down(driver, scroll_pause_time, logging_output_location)
 return save_elements_to_list(driver, start_time, scroll_pause_time, url, logging_output_location)
def time_writer_function(writer_function):
 @functools.wraps(writer_function)
 def wrapper_timer(*args, **kwargs):
  start_time             = time.perf_counter()
  extension           = writer_function.__name__.split('_')[-1]
  timestamp           = kwargs.get('timestamp', 'undeteremined_start_time')
  file_name, new_videos_written, reverse_chronological, logging_output_location = writer_function(*args, **kwargs)
  logging_output_location.writelines(f'{ISOFORMAT(NOW())}: Opening a temp {extension} file and writing ***NEW*** video information to the file....{NEWLINE}')
  end_time            = time.perf_counter()
  total_time             = end_time - start_time
  temp_file           = f'temp_{file_name}_{timestamp}.{extension}'
  final_file             = f'{file_name}.{extension}'
  logging_output_location.writelines(f'{ISOFORMAT(NOW())}: Finished writing to'.ljust(66) + f'{temp_file}{NEWLINE}')
  logging_output_location.writelines(f'{ISOFORMAT(NOW())}: {new_videos_written} ***NEW*** videos written to'.ljust(66) + f'{temp_file}{NEWLINE}')
  logging_output_location.writelines(f'{ISOFORMAT(NOW())}: Closing'.ljust(66) + f'{temp_file}{NEWLINE}')
  if reverse_chronological: os.replace(temp_file, final_file)
  else:      os.remove(temp_file)
  logging_output_location.writelines(f'{ISOFORMAT(NOW())}: Successfully completed write, renamed {temp_file} to {final_file}{NEWLINE}')
  logging_output_location.writelines(f'{ISOFORMAT(NOW())}: It took {total_time} seconds to write the {new_videos_written} ***NEW*** videos to the pre-existing {final_file} {NEWLINE}{NEWLINE}')
 return wrapper_timer
def find_number_of_new_videos(list_of_videos, videos_set):
 visited_on_page = {selenium_element.get_attribute("href") for selenium_element in list_of_videos}
 return len(visited_on_page.difference(videos_set))
def prepare_output(list_of_videos, videos_set, video_number, reverse_chronological):
 new_videos = find_number_of_new_videos(list_of_videos, videos_set)
 total_writes = 0
 if reverse_chronological:
  video_number += new_videos
  incrementer   = -1
 else:
  video_number += 1
  incrementer   = 1
 return video_number, new_videos, total_writes, incrementer
def txt_writer(new_file, old_file, visited_videos, markdown_formatting, reverse_chronological, list_of_videos, spacing, video_number, incrementer, total_writes):
 for selenium_element in list_of_videos if reverse_chronological else list_of_videos[::-1]:
  if selenium_element.get_attribute("href") in visited_videos: continue
  else:
   video_number, total_writes = write.txt_entry(new_file, markdown_formatting, selenium_element, NEWLINE, spacing, video_number, incrementer, total_writes)
   if total_writes % 250 == 0:
    logging_output_location.writelines(f'{ISOFORMAT(NOW())}: {total_writes} new videos written to {new_file.name}...{NEWLINE}')
 if reverse_chronological:
  old_file.seek(0)
  for line in old_file: new_file.write(line)
 else:
  new_file.seek(0)
  for line in new_file: old_file.write(line)
@time_writer_function
def write_to_txt(list_of_videos, file_name, reverse_chronological, logging_output_location, timestamp):
 if 'STORED_IN_TXT' not in locals(): stored_in_txt = store_already_written_videos(file_name, 'txt')
 else:          stored_in_txt = STORED_IN_TXT
 markdown_formatting = False
 spacing    = f'{NEWLINE}' + ' '*4
 with open(f'{file_name}.txt', 'r+', encoding='utf-8') as old_file, open(f'temp_{file_name}_{timestamp}.txt', 'w+', encoding='utf-8') as temp_file:
  video_number          =  int(max(re.findall('^Video Number:\s*(\d+)', old_file.read(), re.M), key = lambda i: int(i)))
  video_number, new_videos, total_writes, incrementer = prepare_output(list_of_videos, stored_in_txt, video_number, reverse_chronological)
  ####### defer to txt_writer() function to find new videos and format updated file #######
  txt_writer(temp_file, old_file, stored_in_txt, markdown_formatting, reverse_chronological, list_of_videos, spacing, video_number, incrementer, total_writes)
 return file_name, new_videos, reverse_chronological, logging_output_location
@time_writer_function
def write_to_md(list_of_videos, file_name, reverse_chronological, logging_output_location, timestamp):
 if 'STORED_IN_MD'  not in locals(): stored_in_md = store_already_written_videos(file_name, 'md')
 else:          stored_in_md = STORED_IN_MD
 markdown_formatting = True
 spacing    = f'{NEWLINE}' + '- ' + f'{NEWLINE}'
 with open(f'{file_name}.md', 'r+', encoding='utf-8') as old_file, open(f'temp_{file_name}_{timestamp}.md', 'w+', encoding='utf-8') as temp_file:
  video_number          =  int(max(re.findall('^Video Number:\s*(\d+)', old_file.read(), re.M), key = lambda i: int(i)))
  video_number, new_videos, total_writes, incrementer = prepare_output(list_of_videos, stored_in_md, video_number, reverse_chronological)
  ####### defer to txt_writer() function to find new videos and format updated file #######
  txt_writer(temp_file, old_file, stored_in_md, markdown_formatting, reverse_chronological, list_of_videos, spacing, video_number, incrementer, total_writes)
 return file_name, new_videos, reverse_chronological, logging_output_location
@time_writer_function
def write_to_csv(list_of_videos, file_name, reverse_chronological, logging_output_location, timestamp):
 if 'STORED_IN_CSV' not in locals(): stored_in_csv = store_already_written_videos(file_name, 'csv')
 else:          stored_in_csv = STORED_IN_CSV
 with open(f'{file_name}.csv', 'r+', newline='', encoding='utf-8') as old_file, open(f'temp_{file_name}_{timestamp}.csv', 'w+', newline='', encoding='utf-8') as temp_file:
  video_number          =  int(max(re.findall('^(\d+)?,', old_file.read(), re.M), key = lambda i: int(i)))
  video_number, new_videos, total_writes, incrementer = prepare_output(list_of_videos, stored_in_csv, video_number, reverse_chronological)
  fieldnames            = ['Video Number', 'Video Title', 'Video URL', 'Watched?', 'Watch again later?', 'Notes']
  writer             = csv.DictWriter(temp_file, fieldnames=fieldnames)
  if reverse_chronological: writer.writeheader()
  for selenium_element in list_of_videos if reverse_chronological else list_of_videos[::-1]:
   if selenium_element.get_attribute("href") in stored_in_csv: continue
   else:
    video_number, total_writes = write.csv_entry(writer, selenium_element, video_number, incrementer, total_writes)
    if total_writes % 250 == 0:
     logging_output_location.writelines(f'{ISOFORMAT(NOW())}: {total_writes} videos written to {temp_file.name}...{NEWLINE}')
  if reverse_chronological:
   old_file.seek(0)
   old_file.readline()
   for line in old_file: temp_file.write(line)
  else:
   temp_file.seek(0)
   for line in temp_file: old_file.write(line)
 return file_name, new_videos, reverse_chronological, logging_output_location
