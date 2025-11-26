
  # 🏏 Sport Intelligence Agent – Architecture & Project Story

  ## 📖 Overview
  The Sport Intelligence Agent is an end-to-end AI application that fetches live sports,
  weather, city insights, and travel data from external APIs, processes it through
  specialized LLM agents using **LangGraph**, and returns a clean, formatted response
  to the user through a **FastAPI UI**.

  This system is fully containerized and deployed on **Azure** with  
  **GitHub Actions → Azure Container Registry → Azure Container Apps**.

  ---

  ## 🎯 Goals
  - Provide live sports data, weather updates, city insights, and travel info.  
  - Route every query to the correct LLM using **intent classification**.  
  - Maintain short-term **session memory** for contextual responses.  
  - Generate a unified final answer using a **Fusion LLM summarizer**.  
  - Deploy a production-ready app using **CI/CD pipelines**.

  ---

  ## 🏗️ Cloud Architecture Diagram ![Architecture Diagram](https://github.com/praveenreddy82472/AI-Powered-Health-Risk-Prediction-Real-Time-Alerting-System-GCP-/blob/main/Images/final_archi.png)

  ## 🧱 Architecture Components

  ### 🔹 FastAPI Backend
  Handles user requests, serves the UI, communicates with LangGraph,
  and manages the session-based memory workflow.

  ### 🔹 HTML + JavaScript UI
  A lightweight UI where users type queries and receive formatted responses.

  ### 🔹 LangGraph Router
  - Classifies user intent  
  - Routes query to correct LLM  
  - Checks and updates session memory  

  ### 🔹 LLM Nodes
  - **Sports-LLM**  
  - **Weather-LLM**  
  - **City-LLM**  
  - **Travel-LLM**  
  - **Fusion-LLM (final summarizer + formatter)**  

  ### 🔹 External APIs Used
  - RapidAPI (Cricket)  
  - OpenWeather  
  - Wikipedia  
  - Azure Maps  

  ### 🔹 CI/CD Pipeline
  GitHub Actions:
  - Build Docker image  
  - Push to **Azure Container Registry**  
  - Deploy to **Azure Container Apps**  

  ---

  ## 🔄 System Flow

  1. User submits a query through the UI  
  2. FastAPI forwards the request to LangGraph  
  3. LangGraph:  
     - Detects intent  
     - Checks session memory  
     - Routes to appropriate LLM node  
  4. LLM node:  
     - Calls necessary external APIs  
     - Extracts and structures data  
  5. Fusion LLM:  
     - Summarizes  
     - Formats final response  
  6. FastAPI → returns answer to UI  

  ---

  ## 📘 Story of the Project

  ### 🔹 Background
  The system was created to combine multiple real-time APIs into  
  **one intelligent conversational agent**.  
  The hard part wasn’t fetching data.  
  The challenge was **routing, organizing, and formatting** everything cleanly.

  ### 🔹 Journey & Learnings
  - Built FastAPI endpoints  
  - Integrated LangGraph for routing  
  - Added session-based memory  
  - Connected all APIs and built custom extractors  
  - Added Fusion LLM for clean unified responses  
  - Designed CI/CD + Azure deployment  
  - Published containerized app to the cloud  

  ---

  ## ⚠️ Challenges & Solutions

  ### 1️⃣ Inconsistent API Data
  **Solution:** Wrote custom cleaning and extraction logic

  ### 2️⃣ Complex Intent Routing
  **Solution:** Tuned LangGraph classifier prompts + fallback flows

  ### 3️⃣ Session Memory Not Working in Azure Containers
  **Solution:** Switched to LangGraph session store (no local file writes)

  ### 4️⃣ API Outputs Were Messy
  **Solution:** Fusion LLM summarizer + formatter

  ---

  ## ☁️ Deployment

  **Cloud:** Microsoft Azure  

  ### Steps:
  - Push code to GitHub  
  - GitHub Actions runs:  
    - Linting  
    - Docker build  
    - Push to ACR  
    - Deploy to Container Apps  
  - Final Web URL generated for public use  

  ---

  ## 🛠️ Tech Stack

  **Backend:** FastAPI  
  **Agents:** LangGraph  
  **LLMs:** Multiple domain-specific nodes  
  **Frontend:** HTML + JavaScript  
  **APIs:** RapidAPI, OpenWeather, Wikipedia, Azure Maps  
  **Cloud:** Azure Container Apps + ACR  
  **CI/CD:** GitHub Actions  

  ---

  ## 🏁 Final Notes
  This system blends multi-agent LLM architecture, real-time API integration,
  session-aware conversation design, and cloud-native deployment.  
  A perfect portfolio project demonstrating modern **AI + Cloud Engineering** skills.

