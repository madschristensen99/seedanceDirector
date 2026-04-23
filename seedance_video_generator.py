import os
import time
from byteplussdkarkruntime import Ark
from dotenv import load_dotenv

load_dotenv()


class SeedanceVideoGenerator:
    def __init__(self, api_key=None, base_url="https://ark.ap-southeast.bytepluses.com/api/v3"):
        self.primary_key = api_key or os.environ.get("ARK_API_KEY")
        self.backup_key = os.environ.get("BACKUP_ARK_API_KEY")
        self.base_url = base_url
        self.using_backup = False
        
        self.client = Ark(
            base_url=base_url,
            api_key=self.primary_key,
        )
    
    def switch_to_backup(self):
        """Switch to backup API key if available"""
        if self.backup_key and not self.using_backup:
            print("\n⚠️  Switching to BACKUP API KEY...")
            self.client = Ark(
                base_url=self.base_url,
                api_key=self.backup_key,
            )
            self.using_backup = True
            return True
        return False
    
    def generate_video(self, prompt, model="seedance-1-5-pro-251215", poll_interval=3, retry_count=0, max_retries=10):
        print("----- Creating video generation request -----")
        
        try:
            create_result = self.client.content_generation.tasks.create(
                model=model,
                content=[
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            )
            
            print(f"Task created with ID: {create_result.id}")
        except Exception as e:
            error_msg = str(e)
            # Check if it's an account overdue error
            if "AccountOverdueError" in error_msg:
                if retry_count < max_retries:
                    if self.backup_key and not self.using_backup and retry_count == 0:
                        # Try backup key first
                        print("⚠️  Account overdue on primary key, switching to backup...")
                        if self.switch_to_backup():
                            return self.generate_video(prompt, model, poll_interval, retry_count + 1, max_retries)
                    
                    # Wait 5 minutes and retry
                    wait_time = 300  # 5 minutes
                    print(f"\n⚠️  AccountOverdueError detected (attempt {retry_count + 1}/{max_retries})")
                    print(f"⏳ Waiting {wait_time // 60} minutes before retrying...")
                    time.sleep(wait_time)
                    print("🔄 Retrying now...")
                    return self.generate_video(prompt, model, poll_interval, retry_count + 1, max_retries)
                else:
                    print(f"❌ Max retries ({max_retries}) reached for AccountOverdueError")
                    raise
            else:
                print(f"❌ ERROR: {error_msg}")
                raise
        
        task_id = create_result.id
        self.current_task_id = task_id
        
        print("\n----- Polling task status -----")
        while True:
            get_result = self.client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            
            if status == "succeeded":
                print("\n----- Task succeeded! -----")
                # Get video URL from content object
                video_url = None
                if hasattr(get_result, 'content') and hasattr(get_result.content, 'video_url'):
                    video_url = get_result.content.video_url
                
                if video_url:
                    print(f"Video URL: {video_url}")
                    return video_url
                else:
                    print(f"Warning: Could not find video_url")
                    raise Exception("Video URL not found in task result")
            elif status == "failed":
                print("\n----- Task failed -----")
                error_msg = str(get_result.error) if hasattr(get_result, 'error') else "Unknown error"
                print(f"Error: {error_msg}")
                
                # Check if it's a copyright/content policy error and we're using Seedance 2.0
                is_copyright_error = any(keyword in error_msg for keyword in [
                    "copyright", "PolicyViolation", "SensitiveContent", 
                    "OutputVideoSensitiveContentDetected"
                ])
                
                if is_copyright_error and "seedance-2" in model.lower():
                    print("\n⚠️  Copyright/content policy error detected with Seedance 2.0")
                    print("🔄 Retrying with Seedance 1.5 (more permissive)...")
                    return self.generate_video(prompt, model="seedance-1-5-pro-251215", poll_interval=poll_interval)
                
                # Raise exception with error info instead of returning non-serializable object
                raise Exception(error_msg)
            else:
                print(f"Current status: {status}, Retrying after {poll_interval} seconds...")
                time.sleep(poll_interval)
    
    def generate_video_with_image(self, prompt, image_url, model="seedance-1-5-pro-251215", poll_interval=3):
        print("----- Creating video generation request with image -----")
        
        create_result = self.client.content_generation.tasks.create(
            model=model,
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        )
        
        print(f"Task created with ID: {create_result.id}")
        
        task_id = create_result.id
        
        print("\n----- Polling task status -----")
        while True:
            get_result = self.client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            
            if status == "succeeded":
                print("\n----- Task succeeded! -----")
                # Get video URL from content object
                video_url = None
                if hasattr(get_result, 'content') and hasattr(get_result.content, 'video_url'):
                    video_url = get_result.content.video_url
                
                if video_url:
                    print(f"Video URL: {video_url}")
                else:
                    print(f"Warning: Could not find video_url")
                return get_result
            elif status == "failed":
                print("\n----- Task failed -----")
                print(f"Error: {get_result.error}")
                return None
            else:
                print(f"Current status: {status}, Retrying after {poll_interval} seconds...")
                time.sleep(poll_interval)


if __name__ == "__main__":
    generator = SeedanceVideoGenerator()
    
    prompt = """Photorealistic style: Under a clear blue sky, a vast expanse of white daisy fields stretches out. 
    The camera gradually zooms in and finally fixates on a close-up of a single daisy, 
    with several glistening dewdrops resting on its petals. 
    --ratio 16:9 --resolution 720p --duration 5 --camerafixed false"""
    
    result = generator.generate_video(prompt)
    
    if result:
        print(f"\n✅ Video generated successfully!")
        print(f"Download your video from: {result.output}")
