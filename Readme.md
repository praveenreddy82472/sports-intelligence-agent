title: "Sport Intelligence Agent - Architecture & Project Story"

overview:
  summary: >
    The Sport Intelligence Agent is an end-to-end AI application that fetches
    live data from multiple external APIs, processes it through specialized
    LLM agents using LangGraph, and presents a clean, formatted final response
    to users through a FastAPI-powered UI. The project is fully containerized
    and deployed on Azure using GitHub Actions and Azure Container Apps.

  goals:
    - Provide live sports data, weather updates, city insights, and travel info.
    - Route each query to the right LLM agent based on user intent.
    - Maintain short session-based memory for contextual conversation.
    - Offer a unified and clean final response using a summarizer + formatter.
    - Deploy a production-ready app through CI/CD pipelines.

architecture:
  components:
    - name: "FastAPI Backend"
      description: >
        Handles user requests, serves the UI, and connects the front-end
        with LangGraph. Also acts as the bridge between session memory and
        the agent router.
    - name: "HTML + JavaScript UI"
      description: >
        Lightweight UI to send prompts to the FastAPI backend and display
        formatted AI responses.
    - name: "LangGraph Router"
      description: >
        Core intelligence layer. It classifies user intent, routes queries
        to the correct LLM node, and manages session-based memory.
    - name: "LLM Nodes"
      list:
        - Sports-LLM
        - Weather-LLM
        - City-LLM
        - Travel-LLM
        - Fusion-LLM (summary + combined insights)
    - name: "APIs Used"
      list:
        - RapidAPI (Cricket)
        - OpenWeather API
        - Wikipedia API
        - Azure Maps API
    - name: "CI/CD Pipeline"
      description: >
        Code is pushed to GitHub, GitHub Actions builds the Docker image,
        pushes it to Azure Container Registry (ACR), and finally deploys it
        to Azure Container Apps.

flow:
  steps:
    - User enters a query in the UI.
    - FastAPI receives the request and sends it to LangGraph.
    - LangGraph:
        - Classifies the intent.
        - Checks session memory.
        - Routes the query to the right LLM node.
    - LLM node:
        - Calls related external APIs.
        - Extracts relevant data.
        - Sends structured information back to LangGraph.
    - Fusion Node:
        - Summarizes and formats all information into a final clean response.
    - FastAPI returns the final answer to UI.

story:
  background: >
    The idea started with a simple need: combine multiple real-time APIs
    into one intelligent agent that understands the user's intent. The
    challenge was not fetching the data—it was organizing it, routing it
    correctly, and making sure the responses felt natural.

  journey:
    - "Built FastAPI services first to verify data flow and UI interaction."
    - "Integrated LangGraph to manage user intent and create multi-agent flow."
    - "Implemented session-based memory to maintain short conversation context."
    - "Connected all external APIs and wrote custom extraction logic."
    - "Used a Fusion LLM to combine raw data into meaningful answers."
    - "Created CI/CD with GitHub Actions."
    - "Containerized the system and deployed to Azure Container Apps through ACR."

challenges:
  - description: >
      External APIs often provide inconsistent or insufficient fields.
    solution: >
      Wrote custom extraction logic to clean, filter, and reshape API responses
      before sending them to LLMs.
  - description: >
      Routing user intent correctly across multiple LLM nodes was complex.
    solution: >
      Fine-tuned LangGraph intent logic with classifier prompts and fallback routing.
  - description: >
      Session-based memory wasn’t persisting inside container environments.
    solution: >
      Switched to session-store based memory inside LangGraph and avoided local
      file writes that containers cannot persist.
  - description: >
      Fusion of multiple API outputs led to messy responses.
    solution: >
      Added a final LLM summarizer + formatter layer to unify the tone and layout.

deployment:
  cloud_platform: "Microsoft Azure"
  steps:
    - Push code to GitHub.
    - GitHub Actions runs:
        - Linting
        - Docker build
        - Push to Azure Container Registry (ACR)
        - Deploy to Azure Container Apps
    - Final URL is used to access the agent.

tech_stack:
  backend: "FastAPI"
  agents: "LangGraph"
  llms: "Multiple custom LLM nodes"
  ui: "HTML + JavaScript"
  apis:
    - RapidAPI Cricket
    - OpenWeather
    - Wikipedia API
    - Azure Maps
  cloud:
    - Azure Container Registry (ACR)
    - Azure Container Apps
  ci_cd: "GitHub Actions"

final_notes: >
  This project combines real-time APIs, multi-agent LLM architecture,
  session memory, and cloud deployment into a single polished solution.
  It is both a technical learning project and a portfolio-ready showcase
  of modern AI + cloud engineering skills.
