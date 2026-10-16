# Google Cloud Deployment Guide — GridMind AI

This guide describes how to deploy the **GridMind AI** multi-factory renewable energy intelligence platform to Google Cloud:
- **Backend**: FastAPI on **Google Cloud Run** (containerized, auto-scaling, serverless).
- **Frontend**: React + Vite + Tailwind SPA on **Firebase Hosting** (global CDN).
- **Secrets**: `GEMINI_API_KEY` stored securely in **Google Cloud Secret Manager**.

---

## 1. Prerequisites

1. [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project <YOUR_PROJECT_ID>
   ```
2. Enable required Google Cloud APIs:
   ```bash
   gcloud services enable \
     run.googleapis.com \
     artifactregistry.googleapis.com \
     cloudbuild.googleapis.com \
     secretmanager.googleapis.com
   ```
3. [Firebase CLI](https://firebase.google.com/docs/cli) installed and logged in:
   ```bash
   npm install -g firebase-tools
   firebase login
   ```

---

## 2. Backend Deployment (Google Cloud Run)

### Step 2.1: Store Gemini API Key in Secret Manager

```bash
echo -n "YOUR_ACTUAL_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --replication-policy="automatic"
```

Grant Cloud Run compute service account permission to read the secret:
```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 2.2: Build and Deploy to Cloud Run

From the `backend/` directory:

```bash
cd backend

# Build and deploy directly from source via Cloud Build
gcloud run deploy gridmind-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production,GEMINI_MODEL=gemini-2.0-flash,GEMINI_REQUEST_TIMEOUT_SECONDS=180" \
  --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest" \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5
```

Upon completion, Cloud Run outputs your Service URL:
```
Service URL: https://gridmind-backend-xyz-uc.a.run.app
```

### Step 2.3: Verify Backend Health

```bash
curl https://gridmind-backend-xyz-uc.a.run.app/health
# Expected: {"status":"ok","service":"GridMind AI","version":"0.1.0",...}
```

---

## 3. Frontend Deployment (Firebase Hosting)

### Step 3.1: Configure Backend Target URL

In `frontend/`: create or update `.env.production`:
```env
VITE_API_BASE_URL=https://gridmind-backend-xyz-uc.a.run.app
```

### Step 3.2: Build Production Bundle

```bash
cd frontend
npm run build
```
This compiles the TypeScript code and produces minified static assets in `frontend/dist/`.

### Step 3.3: Deploy to Firebase Hosting

```bash
# Link project (if not already done)
firebase use <YOUR_FIREBASE_PROJECT_ID>

# Deploy hosting target
firebase deploy --only hosting
```

Firebase Hosting outputs your live URL:
```
Hosting URL: https://gridmind-ai.web.app
```

---

## 4. Final CORS Configuration

Update the Cloud Run service CORS allowed origins to include your live Firebase Hosting domain:

```bash
gcloud run services update gridmind-backend \
  --region us-central1 \
  --update-env-vars="CORS_ORIGINS=https://gridmind-ai.web.app,https://gridmind-ai.firebaseapp.com,http://localhost:5173"
```

---

## 5. Live Production Verification Checklist

- [ ] `GET /health` returns `200 OK`.
- [ ] `GET /api/factories` returns all three demo factories.
- [ ] Factory switching on the frontend refreshes KPIs, charts, and anomalies.
- [ ] `POST /api/optimization/run?factory_id=DEMO-FAC-001` returns `is_feasible: true`.
- [ ] `POST /api/investigation/anomaly/FINDING-PEAK-CAP-H19` invokes Gemini and returns structured root-cause diagnosis.
