import os
import time
import json
from datetime import datetime
from seedance_video_generator import SeedanceVideoGenerator


STAR_WARS_INFINITY_WAR_SCENES = {
    # ACT I: MARVEL MONTAGE & THE RIFT (0:00-1:00)
    "Scene 1: Montage Cold Open (0-12s)": "Rapid-fire montage cut sequence showing Marvel heroes in iconic moments. Quick cuts: Iron Man firing repulsors over New York skyline; Captain America raising shield against charging horde in forest; Thor calling lightning onto ruined Asgardian battlefield; Hulk roaring on Sakaaran arena; Black Widow sliding under debris firing twin pistols; Spider-Man swinging between skyscrapers; Professor Xavier in Cerebro hands at temples glowing; Wolverine mid-leap claws extended; Mister Fantastic stretching across laboratory; Invisible Woman projecting force field over civilians. High-contrast comic-book cinematography, rich color grading, deep reds electric blues radiant golds. Heroic orchestral score with driving percussion. Each hero freeze-frame with bold kinetic typography name stamp. Layered audio: repulsor whines, shield clangs, thunder, roars, claw-snikts building crescendo. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false",
    
    "Scene 2: Thanos Arrives in New York (12-24s)": "Wide establishing shot of midtown Manhattan as swirling blue portal tears open above street, disgorging Thanos - 8-foot purple Titan with cleft chin, gold and blue ceremonial armor, Infinity Gauntlet on left hand holding single glowing blue Space Stone. He lands with concussive impact cracking pavement in spider-web pattern. Cars flip away in slow motion. Pedestrians flee screaming, debris raining from shattered facades. His expression calm, almost sorrowful. He raises Gauntlet, Space Stone pulses, folding reality with blue tesseract-cube energy rippling outward. Smoke, glass, papers spiral through air. New York skyline with afternoon sun catching Chrysler Building. Low sub-bass portal hum, concrete-crunching impact, distant screams, Thanos musical motif deep choral drone with timpani, crystalline chime of Space Stone activating. Photorealistic cinematic rendering. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false",
    
    "Scene 3: Heroes Converge (24-36s)": "Dynamic wide shot of Marvel heroes converging on Thanos from multiple vectors across ruined Manhattan street. Iron Man streaks from above on glowing blue repulsor trails, Captain America runs from street level shield raised, Thor descends in pillar of lightning splitting clouds, Bruce Banner in Hulkbuster exoskeleton crouches behind flipped taxi, Black Widow slides from fire escape, Spider-Man swings on web-line, Professor Xavier's hoverchair glides flanked by Wolverine with claws extended, Mister Fantastic and Invisible Woman arrive in Fantasticar. Heroes form ragged line facing Thanos. Dramatic low-angle cinematography. Captain America speaks firm Brooklyn-inflected voice: 'Everyone, hold the line. Stark — you're the tip of the spear.' Iron Man's faceplate flips up revealing exhausted defiant expression: 'Big purple, meet small angry. Let's dance.' Repulsor hums, shield impacts, thunder, Fantasticar landing jets. Photorealistic rendering. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false",
    
    "Scene 4: The Battle Begins (36-48s)": "High-energy combat sequence in ruined Manhattan as Marvel heroes engage Thanos in coordinated assault. Thor hurls Stormbreaker in lightning arc that Thanos catches bare-handed with Gauntlet, blue Space Stone energy absorbing impact. Iron Man unleashes barrage of micro-missiles while Spider-Man swings low to web Thanos's feet. Captain America throws shield in ricochet pattern off Thanos's armor. Wolverine leaps from rubble with claws raised. Mister Fantastic stretches 40-foot arm to pry Gauntlet while Invisible Woman projects force field around civilians. Thanos uses Space Stone to fold battlefield - street sections warping impossibly, heroes teleported short distances, gravity shifting. Thor shouts Shakespearean Asgardian cadence: 'Bring it down! Bring the whole of Midgard down on his head if we must!' Thanos speaks deep measured voice: 'You are a child fighting the tide.' Dynamic camera, lens flares, dramatic lighting. Clashing energy, impact crunches, Asgardian thunder, Stone's crystalline pulse. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false",
    
    "Scene 5: The Rift Opens (48-60s)": "Catastrophic wide shot of Thanos raising Gauntlet using Space Stone to tear open unstable dimensional rift above Manhattan battlefield - but tear is wrong, jagged, clearly uncontrolled. Portal not blue but chaotic with streaks of green, gold, starfield depth visible through wound in reality. Thanos's eyes widen with first flicker of surprise - he did not intend this. Rift pulls debris, cars, assembled heroes with irresistible gravitational force. Iron Man yanked backward boot-jets firing uselessly. Captain America grabs fire hydrant one-handed. Spider-Man webbed to lamppost being pulled free. Professor Xavier's hoverchair tilts as Wolverine digs claws into asphalt. Thor shouts: 'What sorcery is this?! This is not his portal!' Thanos through gritted teeth: 'Something... older. Reaches through the Stone.' Rift widens, swallows heroes and Thanos in blinding white flash. Tearing-metal shriek of unstable reality, sucking roar of dimensional pull, panicked hero shouts, ominous deep hum of foreign cosmic presence. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false",
    
    # ACT II: ARRIVAL AT ENDOR (1:00-2:00)
    "Scene 6: Emergence Over Endor (60-72s)": "Breathtaking wide establishing shot of forest moon of Endor - lush green canopy, Ewok villages in treetops, debris of second Death Star visible as slow-falling chunks in upper atmosphere creating long streaking meteors of orange flame. Super Star Destroyer hangs in orbit beside Rebel capital ships - uneasy post-battle standoff. Jagged rift tears open in sky above forest canopy, disgorges Marvel heroes in scattered cascade. Iron Man's thrusters ignite stabilizing; Captain America tumbles through tree branches shield-first; Thor rights himself mid-fall with Stormbreaker; Spider-Man catches himself on vine that snaps; Professor Xavier's hoverchair auto-stabilizes with Wolverine gripping arm. Thanos nowhere visible. Rift closes with faint residual shimmer. Distance: TIE fighters and X-wings turn toward disturbance. Star Wars lived-in-universe aesthetic. John Williams Star Wars ambient score motif subtle, alien birdcalls, distant engine whines from orbital fleet, Marvel heroes' grunts and exclamations. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false --style cinematic",
    
    "Scene 7: Heroes in the Forest (72-84s)": "Medium shot of Marvel heroes regrouping in small clearing on Endor forest floor, backlit by shafts of golden afternoon light filtering through enormous redwood-like trees. Scuffed, disoriented, staring at alien sky where two moons faintly visible past debris trails. Iron Man's faceplate retracted, scanning environment with holographic HUD projected from gauntlet, frowning. Captain America has shield slung, helping Black Widow to feet. Spider-Man on low branch looking with wide-eyed wonder. Wolverine sniffing air with deep suspicion. Professor Xavier fingers at temples grimacing. Tony Stark fast New York patter with unease: 'FRIDAY's got nothing. No satellites. No GPS. No cell towers. Nothing she recognizes in the sky.' Peter Parker excited Queens teenager whisper: 'Mr. Stark, those are two moons. There are two moons up there.' Professor Xavier refined mid-Atlantic strained: 'I can feel minds. Thousands. Millions. But they're... distant. Stars-away. And something close — small, furry, curious, watching us right now.' Looks up into trees. Ewok eyes blink from foliage. Rustling leaves, distant bird calls, Stark's HUD hum, ambient mystery. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false --style cinematic",
    
    "Scene 8: The Ewok Encounter (84-96s)": "Comedic wide shot of Marvel heroes surrounded by tribe of Ewoks - small furry bipedal creatures in hooded tunics brandishing primitive spears - emerged from undergrowth and trees. Ewoks cautious but not hostile, jabbering in own language. Wolverine claws half-extended snarling softly. Captain America raises slow palm in universal peace gesture. Spider-Man crouched to Ewok height waving awkwardly. Iron Man's voice through suit speakers sardonic: 'So. This is going great.' Thor strides forward Asgardian theatrical cadence addressing Ewoks: 'Small warriors! We come as allies, not conquerors! Take us to your chieftain that we might parley!' One Ewok points spear at Thor's boot. Black Widow speaks dryly: 'Thor, they don't speak English.' Thor undaunted booms: 'All beings understand respect!' Professor Xavier closes eyes, after moment lead Ewok lowers spear chirps questioningly. Xavier smiles opens eyes: 'I've communicated that we mean no harm. They say... the Jedi will come. Soon. They have sent word.' Ewok chittering, rustle of fur and hide garments, distant forest ambiance, soft hum of Xavier's telepathic concentration. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false --style cinematic",
    
    "Scene 9: The Super Star Destroyer (96-108s)": "Majestic wide shot cutting from forest floor to orbit, revealing Executor-class Super Star Destroyer hanging in space above Endor - 19-kilometer wedge of Imperial grey steel, scarred from Battle of Endor but functional, flying temporary truce banner alongside Rebel signals. Interior command bridge: sleek black panels, blue holographic displays, uniformed officers. Luke Skywalker stands at forward viewport in black Jedi robes, lightsaber on belt, black-gloved prosthetic hand at side. Flanked by mix of Rebel officers in orange jumpsuits and remaining Imperial officers in grey - uneasy post-Endor transitional command. Sandy blonde hair slightly longer than Endor, fresh scar along jawline. Expression contemplative, attuned. Suddenly eyes snap up - senses something. Turns to Rebel officer speaks farm-boy American with new gravity: 'Something just arrived. On the moon. Powerful. Many — and not of this galaxy.' Rebel officer alarmed: 'Commander Skywalker, our sensors didn't register any ships.' Luke quietly: 'They didn't come in a ship. Prep a shuttle. I'm going down alone.' Low ambient hum of Star Destroyer bridge, soft beeps, Force-theme musical motif subtle. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false --style cinematic",
    
    "Scene 10: Luke Descends (108-120s)": "Dramatic medium shot of Imperial Lambda-class shuttle descending through Endor atmosphere with iconic tri-wing configuration, landing gear extending. Shuttle touches down in clearing near Ewok village, steam venting from hydraulics, boarding ramp lowers. Luke Skywalker walks down alone, framed against rising steam and golden forest light, black Jedi robes flowing, lightsaber hilt visible on belt. Expression calm but coiled - fresh from confronting Emperor and redeemed father, carries weight of triumph and grief. Marvel heroes led by Captain America with Ewoks step into clearing to meet him. Heroes visibly process that this young man radiates something never encountered - not magic, not mutation, not Asgardian divinity, but something else. Wolverine growls low: 'I don't like him. He smells... electric.' Professor Xavier awed refined mid-Atlantic: 'Remarkable. His mind is — shielded. Not by training I recognize. By something... ambient. Alive.' Luke's eyes fixed on Xavier. Approaches slowly stops ten feet from group. Shuttle's hydraulic hiss, ramp's mechanical descent, distant Ewok chittering, rustling forest ambiance, reverent silence of first contact. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false --style cinematic",
    
    "Scene 11: 'Obi-Wan?' (120-132s)": "Intimate medium two-shot of Luke Skywalker standing before Professor Charles Xavier's hoverchair in Endor clearing, other Marvel heroes arrayed behind Xavier in loose arc. Luke studies Xavier with confused searching expression - Xavier's bald head, serene bearing, sense of ambient benevolent power, wise elder presence - triggering something in Luke. Luke takes half-step forward, voice quiet almost whisper farm-boy American with new Jedi gravity: 'Obi-Wan?' Beat of stunned silence. Xavier blinks, face softens with kind understanding. Responds refined mid-Atlantic with gentle warmth: 'I'm afraid not, young man. My name is Charles Xavier. But I sense you were expecting... someone who looked rather like me.' Luke's expression flickers - grief, recognition of mistake, embarrassment, curiosity. Tony Stark mutters fast New York patter from background: 'Great. First five seconds and we're already doing ghost-mentor mistaken identity. Love it for us.' Captain America shoots Stark quelling look. Luke's hand drifts toward lightsaber not threatening but wary: 'Then what are you? All of you? The Force tells me you're not of this galaxy. But you're not Sith. You're not... anything I know.' Xavier calmly: 'We would very much like to explain. But we may not have the time. Something followed us here. Something terrible.' Ambient forest sounds, soft hum of Xavier's hoverchair, subtle Force-motif musical cue. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false --style cinematic",
    
    "Scene 12: The Briefing (132-144s)": "Wide shot of Rebel command tent hastily erected in Endor clearing, Marvel heroes gathered around holotable displaying three-dimensional map of galaxy. Princess Leia Organa in Rebel officer uniform stands at one end, brown hair in practical braid, sharp features, commanding presence. Han Solo leans against tent pole in classic smuggler vest arms crossed, Chewbacca beside him growling occasionally. Lando Calrissian stands in cape at communications panel. Luke stands with Professor Xavier, both serving as bridge between groups. Tony Stark speaks quickly explaining: 'So purple Jack-o-lantern has a magic oven mitt. Currently he's got one of six cosmic space-rocks. We think the tear through dimensions scattered the other five somewhere in... this galaxy.' Leia speaks refined Galactic Core accent sharp commanding: 'You're describing objects of immense power. If they're truly scattered across our galaxy, the Empire's remnants, the Hutts, every warlord and cult from Nar Shaddaa to Dathomir will be hunting them within the week.' Han cuts in casual American drawl: 'So what, we babysit a bunch of glowing space-marbles while Captain Grape chases us across the galaxy?' Thor booms: 'We go to war, smuggler! As we did against the Frost Giants!' Han raises eyebrow at Chewbacca who growls back. Han: 'Yeah, pal, I like him too.' Luke quiet authority: 'The Force will guide us to the Stones. It's already pulling at me. I can feel... six points of light across the galaxy. One is very close. Dagobah.' Hum of holotable, ambient tent activity, adventure-theme musical cue. --ratio 16:9 --resolution 720p --duration 12 --camerafixed false --style cinematic",
}


def generate_star_wars_infinity_war_videos(scenes_to_generate=None, output_dir="star_wars_infinity_war_output"):
    os.makedirs(output_dir, exist_ok=True)
    
    generator = SeedanceVideoGenerator()
    results = []
    
    scenes = STAR_WARS_INFINITY_WAR_SCENES
    if scenes_to_generate:
        scenes = {k: v for k, v in STAR_WARS_INFINITY_WAR_SCENES.items() if k in scenes_to_generate}
    
    print(f"\n{'='*80}")
    print(f"STAR WARS: INFINITY WAR - EPISODE VII")
    print(f"{'='*80}")
    print(f"Generating {len(scenes)} scene(s)\n")
    
    for i, (scene_name, prompt) in enumerate(scenes.items(), 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(scenes)}] {scene_name}")
        print(f"{'='*80}\n")
        
        try:
            result = generator.generate_video(prompt, model="seedance-1-5-pro-251215")
            
            if result:
                video_url = None
                if hasattr(result, 'content') and hasattr(result.content, 'video_url'):
                    video_url = result.content.video_url
                
                scene_result = {
                    "scene_name": scene_name,
                    "status": "success",
                    "video_url": video_url if video_url else "not_found",
                    "task_id": result.id if hasattr(result, 'id') else "unknown",
                    "timestamp": datetime.now().isoformat()
                }
                print(f"\n✅ SUCCESS: {scene_name}")
                if video_url:
                    print(f"Video URL: {video_url}")
                else:
                    print(f"Warning: Could not extract video URL")
            else:
                scene_result = {
                    "scene_name": scene_name,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
                print(f"\n❌ FAILED: {scene_name}")
            
            results.append(scene_result)
            
            results_file = os.path.join(output_dir, "star_wars_infinity_war_results.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
        except Exception as e:
            print(f"\n❌ ERROR generating {scene_name}: {str(e)}")
            results.append({
                "scene_name": scene_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    print(f"\n{'='*80}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total scenes: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results if r['status'] in ['failed', 'error'])}")
    print(f"\nResults saved to: {output_dir}/star_wars_infinity_war_results.json")
    
    return results


if __name__ == "__main__":
    import sys
    
    print("\n⚔️ STAR WARS: INFINITY WAR - EPISODE VII 🌌\n")
    print("Epic crossover - Marvel meets Star Wars!")
    print("  Act I: Marvel montage → Thanos battle → dimensional rift")
    print("  Act II: Arrival at Endor → Luke → Rebellion alliance")
    print("  (First 12 scenes of 23 total)")
    
    print("\nOptions:")
    print("1. Generate all 12 scenes")
    print("2. Generate specific scenes")
    print("3. Quick test (Scene 1 only)")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        confirm = input("\n⚠️  This will generate ALL 12 scenes. Continue? (yes/no): ").strip().lower()
        if confirm == "yes":
            print("\n🚀 Generating ALL 12 Star Wars: Infinity War scenes...")
            generate_star_wars_infinity_war_videos()
        else:
            print("Cancelled.")
    elif choice == "2":
        scene_nums = input("Enter scene numbers (comma-separated, e.g., 1,3,6,9,12): ").strip()
        try:
            scene_indices = [int(x.strip()) - 1 for x in scene_nums.split(",")]
            scene_names = [list(STAR_WARS_INFINITY_WAR_SCENES.keys())[i] for i in scene_indices]
            print(f"\n🚀 Generating {len(scene_names)} scene(s)...")
            generate_star_wars_infinity_war_videos(scene_names)
        except (ValueError, IndexError) as e:
            print(f"Error: Invalid scene numbers. Please use numbers 1-12.")
    elif choice == "3":
        print("\n🚀 Generating test scene...")
        first_scene = list(STAR_WARS_INFINITY_WAR_SCENES.keys())[0]
        generate_star_wars_infinity_war_videos([first_scene])
    else:
        print("Invalid choice. Exiting.")
