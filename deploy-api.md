# 🚀 GCP Cloud Run Deployment Guide – Flask API (`spendify-main`)

**Using Dockerfile.api (not default Dockerfile)**

---

## 1️⃣ Set Active GCP Project

```bash
gcloud config set project spendify-mapple-masala
```

---

## 2️⃣ Enable Required Services

```bash
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com
```

---

## 3️⃣ Build & Push Docker Image (using Dockerfile.api)

```bash
gcloud builds submit --tag gcr.io/spendify-mapple-masala/spendify-main --dockerfile Dockerfile.api .
```

---

## 4️⃣ Deploy to Cloud Run (Flask, port 5000)

```bash
gcloud run deploy spendify-main \
  --image gcr.io/spendify-mapple-masala/spendify-main \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --port 5000
```

---

## 5️⃣ Check Logs (optional)

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=spendify-main" \
  --project=spendify-mapple-masala --limit=50 --freshness=1h --format="value(textPayload)"
```

---

## 6️⃣ (Optional) Delete Old Service/Image

```bash
gcloud run services delete spendify-main --region=us-central1

gcloud container images delete gcr.io/spendify-mapple-masala/spendify-main --quiet
```

---

## 📝 Summary Table

| Step            | Command                                                                                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Build Image** | `gcloud builds submit --tag gcr.io/spendify-mapple-masala/spendify-main --dockerfile Dockerfile.api .`                                                                                           |
| **Deploy**      | `gcloud run deploy spendify-main --image gcr.io/spendify-mapple-masala/spendify-main --platform managed --region us-central1 --allow-unauthenticated --memory 1Gi --port 5000`                   |
| **View Logs**   | `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=spendify-main" --project=spendify-mapple-masala --limit=50 --freshness=1h --format="value(textPayload)"` |
| **Delete**      | `gcloud run services delete spendify-main --region=us-central1`<br>`gcloud container images delete gcr.io/spendify-mapple-masala/spendify-main --quiet`                                          |

---

**Cloud Run will give you a public URL after deployment, e.g.:**
`https://spendify-main-xxxxx.a.run.app`