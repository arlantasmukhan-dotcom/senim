# ECHO (Жаңғырық) — Mountain Safe v2
### WIT Teens Hackathon · Case 2 «Mountain Safe: безопасность в горах»

> **"When you can't answer, your phone will."**
> In the mountains you shout and the mountain echoes back. ECHO makes a lost hiker's phone answer the rescuers who are shouting for them.

---

## 0. 200-WORD PITCH SUMMARY (paste-ready, under 200 words)

**Problem.** Rescuers ran 25 operations in Almaty's mountains in 2025, and two people never came home. Rescuers shout, whistle and fly over, but a hiker who is unconscious, hypothermic or asleep cannot answer. Before that, most hikers got lost the same way: they followed a gully downhill into cliffs.

**ECHO turns an ordinary Android phone into an autonomous rescue agent.**

1. **Echo Mode.** After an SOS, a detected fall or a missed return deadline, the phone listens using on-device AI (Google's YAMNet sound model) for shouts, whistles, helicopters and drones. It answers with the 130-year-old Alpine distress signal, flashes its light and plays the hiker's pre-recorded voice: "I'm Aigerim, injured leg, here!"
2. **App-less beacon.** It renames its Bluetooth to `SOS 43.0521 76.9813 LEG`, so any phone scanning nearby sees the coordinates, even without ECHO installed.
3. **Battery sked.** It wakes on a fixed clock schedule, which is sent to rescuers by SMS, so it survives until they arrive.
4. **Trap Map.** Terrain analysis of free elevation data finds gullies that dead-end in cliffs. It warns the hiker before they descend, and the same map tells rescuers where to search first.

---

## 1. Why v1 was dropped
The first version (turnaround coach + Bluetooth relay + SMS SOS) was a remix. HikerAid already computes turnaround/point-of-no-return. Cairn already does overdue alerts. Apple Find My already relays. Judges would have seen it before. **ECHO attacks a gap nobody covers: the moment the victim can no longer help themselves.**

## 2. Understanding the problem (15 pts)

**The two moments that kill:**
| Moment | Reality | Current tools |
|---|---|---|
| **A. The wrong turn** | Lost hikers instinctively go *downhill following water*. SAR teams use this pattern to predict where people end up. In steep ranges, drainages end in waterfalls and cliffs ("cliffed out"). In Almaty: the group lost descending Pik Bashuta (Aug 2025), and groups stuck above Kosmostantsiya after dark. | Maps show the trail, but never *"this gully is a dead end"* |
| **B. The silent victim** | Injured, cold, exhausted or unconscious hikers can't shout back. Ground teams search by *sound sweeps* (shout and listen), and helicopters search by sight. A silent person 50 m away can be missed. | SOS apps need the victim to *act*. Satellite SOS needs an iPhone 14+ in supported countries, or a $300+ device. |

**Target users:** 16–35 year-old casual hikers in Almaty (Big Almaty Lake, Kok-Zhailau, Furmanov, Bashuta) who have phones but no gear. Secondary users: parents, guides, ДЧС rescuers, volunteer SAR teams and drone pilots.

## 3. The solution (20 pts)

### Pillar 1: ECHO MODE, the phone that answers back *(core novelty)*
**Triggers:** manual SOS · fall detection (accelerometer spike + 2 min stillness) · return deadline missed with no check-in.

| Step | What happens | Tech |
|---|---|---|
| Listen | A low-power loudness gate wakes the AI classifier only when there is sound. It detects *Shout/Yell, Whistle, Helicopter, Speech, Aircraft* (all existing YAMNet classes). A detection counts only if it repeats 2+ times in 20 s, to filter river and wind noise. | MediaPipe Audio Classifier + YAMNet (on-device, offline) |
| Answer by sound | Plays the **Alpine distress signal** (6 blasts/min, the international standard since 1894) at max volume, then the hiker's **own recorded voice**: name, injury, "I'm here". | Android AudioTrack, 3 kHz tone (the ear is most sensitive around there) |
| Answer by light | On helicopter/drone detection at night: flashlight + white-screen strobe in the same 6/min pattern. | CameraManager torch |
| Answer by radio | Sets the Bluetooth name to `SOS 43.05214 76.98133 LEG 1412` and becomes discoverable. It also sends a BLE advertisement with the same data for rescuer apps and drones. | BluetoothAdapter.setName, BLE advertiser |
| Survive | **Battery sked:** from the battery % it computes wake windows locked to the clock (e.g. minutes :00–:05 of every 15). The schedule goes into the SOS SMS so rescuers know *when* to shout and scan. At 5 % it sends a final "last-gasp" SMS with location. | BatteryManager, AlarmManager |
| Tell | One 160-character SMS: `ECHO1;43.05214;76.98133;3120m;LEG;B34;SKED:00/15;T1412`, auto-retried when signal appears. | SmsManager |

### Pillar 2: TRAP MAP, prevention computed from terrain *(novelty #2)*
- **Offline algorithm, run once per region:** free Copernicus 30 m elevation data → D8 flow direction/accumulation → find every drainage that branches *downhill off a trail* → trace it downstream. **If it hits a cliff** (slope > 45° over a sustained stretch, or a sharp drop) before reaching another trail or road, it is a **trap corridor**. Merge with known incident points from ДЧС news reports.
- **In the app (offline geofence):** you're > 40 m off-trail, descending, inside a trap corridor → strong vibration + voice: *"Dead end: cliffs about 300 m below. Climb back 80 m north-east to the trail."*
- **Dual use:** trap corridors are where lost hikers end up, so the same layer becomes the **search-priority map** for rescuers. One dataset serves prevention and search.

### Pillar 3: HUNTER, the rescuer side
- **Hunter mode** (same app, rescuer role): scans for ECHO beacons and SOS Bluetooth names and shows a **hot/cold signal-strength meter** + compass for a final approach in fog, bushes or darkness. It also shows the victim's battery sked countdown ("next wake in 04:12, get ready to shout").
- **Drone add-on:** a phone in Hunter mode strapped to any drone sweeps a gully quickly. Unlike the SARDO research drone, it needs no special radio, only a phone.
- **Web dashboard:** SOS pins, trap corridors, last known points.

### Before the hike (minimal on purpose)
A **Trip Card**: route + return deadline + one voice recording + trap-map download. Sent to 2 contacts by SMS/Telegram. It is required to arm the automatic triggers. It is not the novelty, so it stays a 30-second step.

## 4. Novelty (10 pts)
| Idea | Exists? |
|---|---|
| Phone detects rescuers' sounds and **answers automatically** for an unconscious victim | Not found in any rescue product. Only "whistle to find my phone" toys use similar detection. |
| **Bluetooth name as an SOS carrying coordinates**, readable with *no app* | Not documented anywhere I found |
| **Battery sked** shared with rescuers | Borrowed from expedition radio practice, new for phones |
| **Automatic dead-end gully detection** for hikers | Terrain traps are a ski-avalanche concept and drainage following is SAR lore; no consumer auto-warning found |
| Using the Alpine distress signal as the protocol | Real 1894 standard, which adds credibility and a story |

*Honest note:* I can't prove nobody has ever built these. I searched and found nothing similar, so rate the novelty claim as **high but not certain (~80 %)**.

## 5. User value, from every perspective (15 pts)
| Perspective | Value |
|---|---|
| **Hiker** | Protected even when unconscious. Warned *before* the fatal wrong turn. Free. No extra gear. |
| **Parent** | Automatic alert + location + "their phone will answer rescuers". |
| **Rescuer** | Victim location, a sound/light/radio target, when to search (sked) and where to search (trap corridors). |
| **CEO** | Free for hikers. B2G with ДЧС/akimat and Ile-Alatau National Park (bundle with park entry ticket/registration). B2B for tour operators and guides ($5/guide/month), ski resorts (Shymbulak, Oi-Qaragai) and insurers. Moat: the trap-map dataset improves with every incident. |
| **Engineer** | Everything runs on-device and offline. Duty-cycled AI keeps battery use low. Defense against false triggers. The system degrades gracefully: SMS → Bluetooth → sound → light. |
| **Social/global** | Works on a $100 Android phone. Exportable to Kyrgyzstan, Nepal, Georgia and the Caucasus, where satellite gear is unaffordable. |
| **Ethics/privacy** | The microphone is used only in Echo Mode, audio is never stored or sent, and the Bluetooth SOS is only broadcast during an emergency. |

## 6. Impact & scaling (15 pts)
1. **Pilot:** 10 Almaty routes, trap map for Ile-Alatau, a partner hiking club + a ДЧС field test (real rescuers shout, and we measure detection range).
2. **National:** Trip Card integrated with the park checkpoint / tourist registration Almaty is introducing. Hunter mode given to volunteer SAR teams.
3. **Hardware (fits the firmware skills already in this repo):** an ESP32 "Hunter Box" for drones (BLE scanner + LoRa downlink), and a $10 clip-on buzzer for people whose phone dies.
4. **Region:** Central Asia + an iOS version (background audio is more limited on iOS).

**Metrics:** detection range for shout/whistle/helicopter, false-trigger rate per hour, battery hours in Echo Mode, share of hikers who turn back at a trap alert.

## 7. Data & technology (10 pts)
| Tech | Why it's the right choice |
|---|---|
| **Kotlin Android** (not Flutter) | Direct access to Bluetooth naming, audio and torch APIs without plugin fights |
| **MediaPipe Audio Classifier + YAMNet** | Pretrained on 521 sound classes, including the exact ones needed. Offline, and the official Android sample gives a head start. |
| **Copernicus GLO-30 DEM + pysheds/WhiteboxTools** | Free terrain data. Flow analysis is a standard hydrology method, reused for safety. |
| **OSM trails** | Free trail geometry |
| **SmsManager / BLE / BluetoothAdapter** | Work with zero internet |
| **Supabase + Telegram Bot** | Free backend for deadline alerts |
| **Leaflet** | Rescuer dashboard |

**Known limits (say them before judges do):** loud rivers mask sound (fixed by repetition filtering; test range near water). A phone speaker reaches tens of metres to about 200 m, less than a whistle. 30 m elevation data misses small cliffs, so incident data refines it. Bluetooth range is about 50–100 m in the open. Android-first.

## 8. Demo & pitch (10 pts): the 2-minute video
1. **0:00** Black screen, the sound of a rescuer shouting "Эй! Есть кто?", then silence. *"If you can't answer, they walk past you."*
2. **0:15** Trail on the map. The hiker steps into a gully, and the phone says "Dead end, cliffs below, go back north-east."
3. **0:40** A fall is detected, Echo Mode starts, and the SMS arrives on mom's phone.
4. **1:00** **The wow moment:** a teammate shouts from 30 m away, and the phone answers with a siren + "I'm Aigerim, injured leg, here!" + strobe.
5. **1:25** Any stranger's phone opens its Bluetooth list and sees `SOS 43.05214 76.98133 LEG`.
6. **1:40** Rescuer Hunter meter goes hot → found. Scaling slide.

**Live on stage:** let a judge shout, and the phone answers. People remember what they took part in.

## 9. Case fit (5 pts)
✔ Prevents danger before it's critical (Trap Map) ✔ Cuts rescue time (Echo, beacon, sked, Hunter) ✔ Built *for* zero connectivity ✔ Working MVP ✔ **Captain must be female**

---

## 10. 48-hour MVP build plan (team of 4)
| Hours | Mobile dev (Kotlin) | Data/GIS | Backend/web | Captain |
|---|---|---|---|---|
| 0–6 | Clone MediaPipe audio sample, get shout/whistle detection working | Download DEM for Ile-Alatau, run flow accumulation | Supabase + Telegram bot | Interview 3 hikers, call ДЧС press office |
| 6–18 | Echo response: siren pattern, voice playback, torch | Trap-corridor script → GeoJSON | Deadline alert (dead-man switch) | UX flows, Trip Card screen |
| 18–30 | Bluetooth SOS name + BLE advert + SMS | Trap geofence logic in app | Dashboard (Leaflet) | Deck draft |
| 30–40 | Hunter mode (hot/cold meter), battery sked | Validate traps on Bashuta/Furmanov | SMS parser → pins | Video script |
| 40–48 | **Field test outdoors near a stream**, fix false triggers | Numbers for the deck | Deploy | Record video, rehearse |

## 11. Learning roadmap (in order)
1. **Kotlin + Android basics.** Android Basics with Compose (free Google course), first 3 units.
2. **Android permissions & foreground services** (mic, location, Bluetooth, SMS).
3. **MediaPipe Audio Classifier**: run the official Android sample, read YAMNet's class list.
4. **Basic DSP**: loudness gating, why 3 kHz, debouncing detections.
5. **Android Bluetooth**: classic discovery/setName, BLE advertising & scanning, RSSI.
6. **SmsManager + AlarmManager** (exact alarms for the sked).
7. **GIS with Python**: rasterio, DEMs, slope, D8 flow direction/accumulation (pysheds tutorial).
8. **GeoJSON + geofencing** on Android.
9. **Supabase + Telegram Bot API.**
10. **Leaflet.js** dashboard.
11. **SAR knowledge**: Koester's *Lost Person Behavior* (drainage following), the Alpine distress signal, sound-sweep search.
12. **Pitching**: problem → live demo → impact.
13. *(Phase 2)* ESP32 BLE scanning + LoRa.

## 12. Sources & inspiration
- **Mountain echo / "shout and the mountain answers"**: the core metaphor (own idea).
- Find-my-phone whistle apps, proof that sound detection on phones works: https://play.google.com/store/apps/details?id=com.kl.whistleapp.findphone
- Alpine distress signal (1894): https://en.wikipedia.org/wiki/Alpine_distress_signal
- SARDO drone locating phones: https://spectrum.ieee.org/searchandrescue-drone-locates-victims-by-homing-in-on-their-phones · Wi-Fi drone SAR paper: https://arxiv.org/pdf/2604.09115
- Why phones fail as avalanche beacons (so ECHO does not claim that): https://www.cbc.ca/news/canada/british-columbia/avalanche-beacon-phone-apps-risk-lives-experts-say-1.2252142
- Drainage following / "cliffed out" hikers: https://www.outdoors.org/resources/amc-outdoors/appalachia/day-four-a-rescuers-account-of-a-hikers-baffling-survival/
- Koester ISRID: https://www.d4h.com/blog/dr-robert-koesters-lost-person-behavior-and-how-to-contribute-to-isrid
- Terrain traps (ski concept, reused for hiking): https://www.snowfeetstore.com/blogs/snowfeet_skiskates_skiboards_snowblades_skiblades_mini_skis_short_skis/terrain-traps-backcountry-skiing-avoid
- Existing tools ECHO avoids copying: HikerAid (turnaround) https://hikeraid.onrender.com/ · Cairn https://www.cairnme.com/
- Almaty data: https://www.zakon.kz/proisshestviia/6488649-turisty-zabludilis-v-gorakh-almaty.html · https://informburo.kz/cards/kakie-opasnosti-podsteregaiut-turistov-v-almatinskix-gorax-i-kak-s-nimi-spravliatsia-spasateli · https://exclusive.kz/v-almaty-vvodjat-registraciju-turistov-pered-pohodami-v-gory/
