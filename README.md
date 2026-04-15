# TempSchedPlus

Intelligent temperature-aware storage management across device, edge, and cloud with cold-data compression and encryption.

## Firebase + API Setup

1. Install dependencies:

	```powershell
	pip install -r requirements.txt
	```

2. Put your Firebase service account key in the project root as `firebase_key.json`.

3. Set your Firebase bucket and optional flags:

	```powershell
	$env:FIREBASE_STORAGE_BUCKET="your-project-id.appspot.com"
	$env:FIREBASE_KEY_FILE="firebase_key.json"
	$env:TEMPSCHED_ENABLE_UPLOAD_ENCRYPTION="1"
	$env:TEMPSCHED_DELETE_AFTER_UPLOAD="0"
	```

4. Run backend API + scheduler loop:

	```powershell
	uvicorn main:app --reload
	```

5. Fetch cloud metadata from frontend:

	```javascript
	useEffect(() => {
	  fetch("http://localhost:8000/files")
		 .then((res) => res.json())
		 .then((data) => setFiles(data));
	}, []);
	```
