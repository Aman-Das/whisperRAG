**#NoteNinja - MeetFlow**


Project Documentation: MeetFlow - AI-Powered Meeting Assistant

Project Overview
MeetFlow is a cutting-edge meeting assistant that revolutionizes how teams capture and act on discussions. By combining real-time transcription with AI-driven insights, MeetFlow transforms raw audio into structured summaries, actionable task lists, and keyword highlights. Designed for modern workplaces, it ensures no detail is missed and every decision is actionable.

Key Features
Real-Time Transcription: Powered by Vosk, a state-of-the-art speech-to-text model, delivering 95%+ accuracy even in noisy environments.
Context-Aware Summaries: Leverages LLM (Large Language Models) to generate concise, context-rich summaries with decision points and deadlines.
Task Automation: Extracts action items and assigns them to participants using advanced NLP techniques.
Offline-First Architecture: Processes sensitive data locally, ensuring privacy and reducing latency.
Collaborative Interface: A sleek React-based dashboard for team annotations and edits.
Summary Transcripts & Timestamps: Generates detailed meeting transcripts with timestamps for easy reference.
Keyword Extraction: Automatically identifies and highlights important keywords throughout the meeting.
Sentiment Analysis: Analyzes speaker sentiment during the meeting to provide insights into team mood and decision-making dynamics.
Technical Architecture
Backend: Built on Flask, with Vosk for real-time transcription and LLM for intelligent summarization.
Frontend: A responsive React.js interface with a modern, Notion-inspired design.
Hosting: Initially deployed on AWS EC2 for scalable performance, with PM2 ensuring 24/7 uptime. However, due to hardware limitations and latency issues with third-party hosting, the system is now hosted on localhost for optimal performance.
Audio Processing: Utilizes Librosa for high-quality audio preprocessing, ensuring optimal input for Vosk.
Deployment & Scalability
MeetFlow is currently hosted on localhost to address latency issues encountered with third-party hosting. This local deployment ensures faster response times and better utilization of available hardware resources. The use of PM2 as a process manager ensures seamless operation of both backend and frontend services. This robust infrastructure supports future expansion, including integrations with popular collaboration tools and advanced AI features.

Future Scope
UI Expansion: A ready-to-implement UI design is prepared to support upcoming features like real-time collaborative editing and advanced analytics dashboards.
Enterprise Integration: Planned compatibility with Zoom, Microsoft Teams, and Slack.
Enhanced AI: Roadmap includes emotion analysis, predictive task assignment, and multi-language support.
Team & Recognition
Developed during AISOC’S CHRONOS v1.0 Hackathon, MeetFlow stands out for its innovative use of Vosk and LLM to deliver a privacy-conscious, AI-powered productivity tool. The project has been recognized for its practical applications and technical excellence, making it a strong contender in the hackathon.

Made with ☕(Flask)

For implementation details or collaboration inquiries, contact the development team.