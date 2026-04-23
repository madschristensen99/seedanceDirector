#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading

sys.path.insert(0, str(Path(__file__).parent.parent))
from seedance_video_generator import SeedanceVideoGenerator

# Global lock for file writes
results_lock = threading.Lock()

def load_scenes(json_file):
    with open(json_file, 'r') as f:
        scenes = json.load(f)
    print(f"\n{'='*80}")
    print(f"LOADED {len(scenes)} SCENES FROM {json_file}")
    print(f"{'='*80}\n")
    return scenes

def generate_single_scene(scene_data, output_dir, results_file):
    scene_num = scene_data['scene_number']
    scene_name = scene_data['scene_name']
    duration = scene_data['duration']
    prompt = scene_data['original_prompt']
    
    print(f"\n🎬 Starting Scene {scene_num}: {scene_name[:60]}... (Duration: {duration}s)")
    
    generator = SeedanceVideoGenerator()
    
    full_prompt = f"{prompt} --resolution 1080p --duration {duration}"
    
    try:
        video_url = generator.generate_video(
            prompt=full_prompt,
            model="dreamina-seedance-2-0-260128"
        )
        
        task_id = getattr(generator, 'current_task_id', 'unknown')
        
        result = {
            "scene_number": scene_num,
            "scene_name": scene_name,
            "duration": duration,
            "status": "success",
            "video_url": video_url,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Scene {scene_num} completed successfully!")
        
        with results_lock:
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                results = []
            
            results.append(result)
            results.sort(key=lambda x: x['scene_number'])
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Scene {scene_num} failed: {error_msg}")
        
        # Detect if it's a copyright/content policy error
        is_copyright_error = any(keyword in error_msg.lower() for keyword in [
            "copyright", "policyviolation", "sensitivecontent", 
            "outputvideosensitivecontentdetected", "outputaudiosensitivecontent"
        ])
        
        # Log copyright failures to separate file
        if is_copyright_error:
            copyright_log = {
                "scene_number": scene_num,
                "scene_name": scene_name,
                "duration": duration,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            
            copyright_log_file = str(Path(results_file).parent / "copyright_failures.json")
            with results_lock:
                try:
                    with open(copyright_log_file, 'r') as f:
                        copyright_logs = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    copyright_logs = []
                
                copyright_logs.append(copyright_log)
                copyright_logs.sort(key=lambda x: x['scene_number'])
                
                with open(copyright_log_file, 'w') as f:
                    json.dump(copyright_logs, f, indent=2)
            
            print(f"📝 Copyright failure logged to {copyright_log_file}")
        
        result = {
            "scene_number": scene_num,
            "scene_name": scene_name,
            "duration": duration,
            "status": "failed",
            "error": error_msg,
            "error_type": "copyright" if is_copyright_error else "other",
            "timestamp": datetime.now().isoformat()
        }
        
        with results_lock:
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                results = []
            
            results.append(result)
            results.sort(key=lambda x: x['scene_number'])
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
        
        return result

def generate_videos_parallel(scenes_list, max_workers=3, output_dir="snow_crash_output", results_file="snow_crash_results.json"):
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(results_file):
        with open(results_file, 'w') as f:
            json.dump([], f)
    
    try:
        with open(results_file, 'r') as f:
            existing_results = json.load(f)
    except json.JSONDecodeError:
        print("⚠️  Corrupted results file detected, resetting...")
        existing_results = []
        with open(results_file, 'w') as f:
            json.dump([], f)
    
    completed_scenes = {r['scene_number'] for r in existing_results if r.get('status') == 'success'}
    
    scenes_to_generate = [s for s in scenes_list if s['scene_number'] not in completed_scenes]
    
    if not scenes_to_generate:
        print("\n✅ All scenes already generated!")
        return existing_results
    
    print(f"\n{'='*80}")
    print(f"PARALLEL GENERATION: {len(scenes_to_generate)} scenes remaining")
    print(f"Already completed: {len(completed_scenes)} scenes")
    print(f"Max workers: {max_workers}")
    print(f"{'='*80}\n")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_single_scene, scene, output_dir, results_file): scene
            for scene in scenes_to_generate
        }
        
        try:
            for future in as_completed(futures):
                scene = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    print(f"❌ Unexpected error for scene {scene['scene_number']}: {e}")
        except KeyboardInterrupt:
            print("\n\n⚠️  Keyboard interrupt detected. Shutting down gracefully...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise
    
    print(f"\n{'='*80}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*80}\n")
    
    with open(results_file, 'r') as f:
        all_results = json.load(f)
    
    successful = sum(1 for r in all_results if r.get('status') == 'success')
    failed = sum(1 for r in all_results if r.get('status') == 'failed')
    copyright_errors = sum(1 for r in all_results if r.get('status') == 'failed' and r.get('error_type') == 'copyright')
    other_errors = failed - copyright_errors
    
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"   ⚠️  Copyright/Content Policy: {copyright_errors}")
    print(f"   ⚠️  Other Errors: {other_errors}")
    print(f"📊 Total: {len(all_results)}")
    
    return all_results

def main():
    script_dir = Path(__file__).parent
    scenes_file = script_dir / "advanced_json" / "all_sequences_combined.json"
    results_file = script_dir / "snow_crash_results.json"
    output_dir = script_dir / "snow_crash_output"
    
    scenes = load_scenes(scenes_file)
    
    results = generate_videos_parallel(
        scenes,
        max_workers=3,
        output_dir=str(output_dir),
        results_file=str(results_file)
    )

if __name__ == "__main__":
    main()
