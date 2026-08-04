# VictoriaOS Roadmap

## Core Platform

- [x] Configuration
- [x] Logging
- [x] Database (SQLite via SQLAlchemy)
- [x] Memory (persistent, survives restarts)
- [x] Brain / Orchestrator
- [x] Skills
- [ ] Security (auth, secrets rotation, request signing)

## Voice

- [x] Wake word ("Hello Victoria")
- [x] Voice activity detection / silence detection / interruption handling
- [x] Speech-to-text (OpenAI)
- [x] Text-to-speech (OpenAI)
- [x] Conversation mode (multi-turn without repeating the wake word)
- [ ] Speaker verification (needs enrolled voiceprint + embedding model)
- [ ] On-device ReSpeaker microphone integration (needs real hardware)

## Intelligence

- [x] OpenAI integration
- [x] AI Context Builder (history + preferences + tasks -> every GPT call)
- [ ] Reasoning / planning beyond single-turn GPT calls
- [ ] Proactive memory retrieval (semantic search / embeddings)

## Productivity

- [x] Yahoo Mail
- [x] Tasks (create/complete/delete/list + due-task polling)
- [ ] Gmail
- [ ] Calendar
- [ ] Contacts
- [ ] Notes
- [ ] Reminders (scheduled delivery, not just polling)

## Communications

- [ ] Calls
- [ ] SMS
- [ ] WhatsApp (future)

## Travel

- [ ] Flights
- [ ] Hotels
- [ ] Rental cars

## Vehicle

- [ ] BMW

## Home

- [ ] Home Assistant
- [ ] Thermostat
- [ ] Cameras
- [ ] Lights
- [ ] Locks

## Future

- [ ] Vision
- [ ] Mobile app
- [ ] Apple Watch
- [ ] Android
- [ ] Multi-room
