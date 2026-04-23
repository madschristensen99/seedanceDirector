#!/usr/bin/env python3
"""
Incremental video inserter.
Downloads scenes and inserts them into the merged video at the correct timestamp.
"""
import json
import os
import time
import subprocess
from pathlib import Path
import requests

def download_video(url, output_path, timeout=60):
    """Download a video from URL to output_path"""
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        start_time = time.time()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                if time.time() - start_time > 120:
                    raise TimeoutError("Download exceeded 2 minutes")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def get_video_duration(video_path):
    """Get duration of a video file in seconds"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 0

def insert_scene_at_timestamp(existing_video, new_scene, output_video, insert_time):
    """Insert a new scene into existing video at specified timestamp"""
    temp_before = "temp_before.mp4"
    temp_after = "temp_after.mp4"
    concat_list = "temp_concat.txt"
    
    try:
        # Split existing video at insertion point
        # Part 1: From start to insert_time
        if insert_time > 0:
            cmd_before = [
                'ffmpeg', '-y',
                '-i', existing_video,
                '-t', str(insert_time),
                '-c', 'copy',
                temp_before
            ]
            subprocess.run(cmd_before, check=True, capture_output=True)
        
        # Part 2: From insert_time to end
        cmd_after = [
            'ffmpeg', '-y',
            '-i', existing_video,
            '-ss', str(insert_time),
            '-c', 'copy',
            temp_after
        ]
        subprocess.run(cmd_after, check=True, capture_output=True)
        
        # Create concat list
        with open(concat_list, 'w') as f:
            if insert_time > 0:
                f.write(f"file '{os.path.abspath(temp_before)}'\n")
            f.write(f"file '{os.path.abspath(new_scene)}'\n")
            f.write(f"file '{os.path.abspath(temp_after)}'\n")
        
        # Concatenate all parts (re-encode for compatibility)
        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-f', 'mp4',
            output_video
        ]
        result = subprocess.run(cmd_concat, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd_concat)
        
        return True
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        return False
    finally:
        # Cleanup temp files
        for f in [temp_before, temp_after, concat_list]:
            if os.path.exists(f):
                os.remove(f)

def calculate_insert_position(all_scenes, scene_number):
    """Calculate timestamp where this scene should be inserted based on previous scenes"""
    insert_time = 0.0
    for scene in sorted(all_scenes, key=lambda x: x['scene_number']):
        if scene['scene_number'] >= scene_number:
            break
        if scene['status'] == 'success':
            insert_time += scene['duration']
    return insert_time

def monitor_and_insert(results_json_path, videos_dir, output_video, poll_interval=10):
    """Monitor results JSON and insert videos as they complete"""
    os.makedirs(videos_dir, exist_ok=True)
    
    processed_scenes = set()
    failed_attempts = {}
    all_scenes_data = []
    
    print("=" * 80)
    print("🎬 Incremental Video Inserter")
    print("=" * 80)
    print(f"📁 Monitoring: {results_json_path}")
    print(f"💾 Videos dir: {videos_dir}")
    print(f"🎥 Output: {output_video}")
    print(f"⏱️  Poll interval: {poll_interval}s")
    print("=" * 80)
    
    while True:
        try:
            if not os.path.exists(results_json_path):
                print(f"⏳ Waiting for {results_json_path}...")
                time.sleep(poll_interval)
                continue
            
            with open(results_json_path, 'r') as f:
                results = json.load(f)
            
            all_scenes_data = results
            
            # Find new successful scenes
            new_scenes = []
            for scene in results:
                scene_num = scene['scene_number']
                if scene['status'] == 'success' and scene_num not in processed_scenes:
                    new_scenes.append(scene)
            
            # Process new scenes in order
            for scene in sorted(new_scenes, key=lambda x: x['scene_number']):
                scene_num = scene['scene_number']
                scene_name = scene['scene_name']
                video_url = scene['video_url']
                scene_path = os.path.join(videos_dir, f"scene_{scene_num:03d}.mp4")
                
                # Skip if failed too many times
                if failed_attempts.get(scene_num, 0) >= 3:
                    print(f"⏭️  Skipping Scene {scene_num} (failed 3 times)")
                    continue
                
                print(f"\n📥 Downloading Scene {scene_num}: {scene_name}")
                
                if not download_video(video_url, scene_path):
                    failed_attempts[scene_num] = failed_attempts.get(scene_num, 0) + 1
                    print(f"⚠️  Failed (attempt {failed_attempts[scene_num]}/3)")
                    continue
                
                print(f"✅ Downloaded: scene_{scene_num:03d}.mp4")
                
                # Calculate where to insert this scene
                insert_time = calculate_insert_position(all_scenes_data, scene_num)
                
                print(f"🔧 Inserting at timestamp {insert_time:.2f}s...")
                
                # If this is the first scene or output doesn't exist, just copy it
                if not os.path.exists(output_video) or len(processed_scenes) == 0:
                    subprocess.run(['cp', scene_path, output_video], check=True)
                    print(f"✅ Created initial video")
                else:
                    # Insert into existing video
                    temp_output = output_video.replace('.mp4', '_temp.mp4')
                    if insert_scene_at_timestamp(output_video, scene_path, temp_output, insert_time):
                        os.replace(temp_output, output_video)
                        file_size = os.path.getsize(output_video) / (1024 * 1024)
                        print(f"✅ Inserted! New size: {file_size:.1f}MB")
                    else:
                        print(f"⚠️  Insert failed, will retry later")
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                        continue
                
                processed_scenes.add(scene_num)
                failed_attempts.pop(scene_num, None)
            
            # Show status
            total_scenes = len(results)
            successful = len([s for s in results if s['status'] == 'success'])
            failed = len([s for s in results if s['status'] == 'failed'])
            
            print(f"\n📊 Status: {len(processed_scenes)}/{successful} inserted | "
                  f"{successful} success | {failed} failed | {total_scenes} total")
            
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(poll_interval)
    
    # Final summary
    if processed_scenes:
        file_size = os.path.getsize(output_video) / (1024 * 1024)
        print(f"\n{'=' * 80}")
        print(f"✅ Complete! Final video: {output_video}")
        print(f"📊 Total scenes: {len(processed_scenes)}")
        print(f"💾 File size: {file_size:.1f}MB")
        print(f"{'=' * 80}")

def main():
    script_dir = Path(__file__).parent
    results_json = script_dir / "snow_crash_results.json"
    videos_dir = script_dir / "downloaded_videos"
    output_video = script_dir / "snow_crash_merged.mp4"
    
    monitor_and_insert(
        results_json_path=str(results_json),
        videos_dir=str(videos_dir),
        output_video=str(output_video),
        poll_interval=10
    )

if __name__ == "__main__":
    main()
