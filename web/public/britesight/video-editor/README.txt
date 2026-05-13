BriteSight Video Editor - step31.5 safari video handoff fix

This version keeps the Safari/audio fixes and adds smoother video-to-video handoff by prestarting the next video element muted/hidden shortly before the current clip ends, then switching visibility at the clip boundary.

BriteSight Video Editor - step31.3-smooth-clip-start-fix

Changes:
- Added a monotonic timeline guard during playback so browser video time jitter cannot move the playhead backwards at clip boundaries.
- Delays timeline updates for a new video clip until the clip is seeked and playback is actually armed.
- Cancels old requestAnimationFrame loops during clip handoff.
- Clears all old preview video handlers when playback is stopped or when changing clips.
- Keeps Safari preview compatibility fixes from step31.0 and handoff cleanup from step31.1.

Notes:
- Safari still requires Safari-supported video codecs for live preview. MP4/MOV with H.264 is safest.

Step 31.6: Safari gapless handoff adjustment. Prestarts the next clip earlier, swaps to a prestarted clip before pausing the outgoing video, and hands off slightly before Safari reaches the hard end frame to avoid the visible micro-stop between clips.
