# PARA AI Demo Checklist

Use this list immediately before presenting. Check every item in the same environment used for the demo.

- [ ] Backend virtual environment is active and `uvicorn main:app --reload` starts cleanly.
- [ ] Frontend dependencies are installed and `npm run dev` starts cleanly.
- [ ] `http://localhost:8000/docs` loads and shows all workflow endpoints.
- [ ] Bike-Helmet-Detectionv2 weights exist at the configured `BIKE_HELMET_MODEL_PATH`.
- [ ] PeterHdd pothole weights exist at the configured `MODEL_PATH`.
- [ ] PaddleOCR can initialize in the demo environment.
- [ ] A small, valid MP4/MOV/AVI has been prepared for upload.
- [ ] Upload returns a report ID and meaningful validation errors for an invalid file.
- [ ] Analysis reads the whole clip and progress reaches 100%.
- [ ] A motorcycle without a helmet creates a helmet incident when model labels support it.
- [ ] Pedestrian and car footage creates no helmet incident.
- [ ] A pothole creates a pothole incident; ordinary road and cracks do not.
- [ ] A visible plate is read; an unreadable plate is shown as `UNKNOWN`.
- [ ] Evidence timestamps match the source video playback.
- [ ] Approve and reject actions update the incident status.
- [ ] Mock submission returns a `PARA-…` tracking ID.
- [ ] Dashboard values update after review/submission.
- [ ] README, project summary, and this checklist are present.
- [ ] `pytest` and `npm run build` have passed in the presentation environment.
- [ ] `git status` is clean after the final commit and `git push` is verified.
