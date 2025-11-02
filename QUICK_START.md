# Quick Start Guide

## 🚀 5-Minute Backend Setup

### Prerequisites
- Python 3.8+ installed
- MongoDB installed (or MongoDB Atlas account)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with these minimum settings:
```env
# MongoDB (REQUIRED)
MONGODB_URI=mongodb://localhost:27017/answer_evaluation_system

# Security (REQUIRED - change these!)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Frontend URL (REQUIRED)
FRONTEND_URL=http://localhost:3000

# OpenAI API (optional - for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Step 3: Start Backend
```bash
python app.py
```

Backend will be running at: `http://localhost:5000`

### Step 4: Test Backend
Open your browser or use curl:
```bash
# Test health endpoint
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","database":"connected","nlp_models":"not loaded"}
```

## Frontend Integration

### Vue.js Example
1. Install axios: `npm install axios`
2. Add to your main.js:
```javascript
import axios from 'axios'
import VueAxios from 'vue-axios'

Vue.use(VueAxios, axios)
Vue.prototype.$http = axios.create({
  baseURL: 'http://localhost:5000/api'
})
```

### Test Login
```javascript
// Test login endpoint
this.$http.post('/auth/login', {
  email: 'test@example.com',
  password: 'TestPass123'
}).then(response => {
  console.log('Login successful:', response.data)
}).catch(error => {
  console.error('Login failed:', error.response.data)
})
```

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register teacher |
| POST | `/api/auth/login` | Login teacher |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/evaluation-schemes` | Create evaluation scheme |
| GET | `/api/evaluation-schemes` | List evaluation schemes |
| POST | `/api/answer-sheets/bulk` | Upload answer sheets |
| GET | `/api/files/:id` | Download PDF files |

## Next Steps

1. Read `FRONTEND_INTEGRATION.md` for detailed integration guide
2. Check `API_ENDPOINTS.md` for complete API documentation
3. Start building your Vue/Nuxt frontend components

## Troubleshooting

**Backend won't start:**
- Check MongoDB is running
- Verify MONGODB_URI in .env
- Install missing dependencies: `pip install -r requirements.txt`

**CORS errors:**
- Verify FRONTEND_URL matches your frontend URL
- Restart backend after changing .env

**401 Unauthorized errors:**
- Check JWT token is being sent in Authorization header
- Verify token format: `Bearer <token>`

That's it! Your backend is ready for frontend integration. 🎉