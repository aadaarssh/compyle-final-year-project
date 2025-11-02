# Frontend Integration Guide

## Quick Start for Vue/Nuxt Frontend Integration

This guide will help you connect your Vue/Nuxt frontend to the Flask backend API.

### 1. Backend Setup

#### 1.1 Install Dependencies
```bash
cd compyle-final-year-project
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

#### 1.2 Environment Configuration
```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-very-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Server Configuration
PORT=5000
HOST=0.0.0.0

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/answer_evaluation_system

# OpenAI Configuration (required for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Redis Configuration (for background tasks)
REDIS_URL=redis://localhost:6379/0

# CORS Configuration - IMPORTANT!
FRONTEND_URL=http://localhost:3000  # Change to your frontend URL

# File Upload Limits
MAX_FILE_SIZE_MB=10
MAX_BULK_UPLOAD=50
```

#### 1.3 Start the Backend Server
```bash
python app.py
```

The backend will be running at: `http://localhost:5000`

### 2. Frontend Configuration

#### 2.1 Axios API Service Setup

Create an API service file in your Vue/Nuxt project:

**For Vue.js:**
```javascript
// src/services/api.js
import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// Request interceptor - Add JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - Handle 401 errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Clear local storage
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      // Redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

**For Nuxt.js:**
```javascript
// plugins/api.js
import axios from 'axios'

export default function ({ $axios, store, redirect }) {
  $axios.defaults.baseURL = 'http://localhost:5000/api'

  // Request interceptor
  $axios.onRequest(config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // Response interceptor
  $axios.onError(error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      redirect('/login')
    }
  })
}
```

#### 2.2 Environment Variables

**For Vue.js (.env):**
```env
VUE_APP_API_BASE_URL=http://localhost:5000/api
```

**For Nuxt.js (nuxt.config.js):**
```javascript
export default {
  env: {
    API_BASE_URL: 'http://localhost:5000/api'
  }
}
```

### 3. Authentication Integration

#### 3.1 Authentication Service

Create an authentication service:

```javascript
// src/services/auth.js
import api from './api'

export default {
  async login(email, password) {
    const response = await api.post('/auth/login', {
      email,
      password
    })

    // Store token and user data
    localStorage.setItem('token', response.data.token)
    localStorage.setItem('user', JSON.stringify(response.data.user))

    return response.data
  },

  async register(email, password, name) {
    const response = await api.post('/auth/register', {
      email,
      password,
      name
    })

    // Store token and user data
    localStorage.setItem('token', response.data.token)
    localStorage.setItem('user', JSON.stringify(response.data.user))

    return response.data
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me')
    return response.data.user
  },

  logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },

  isAuthenticated() {
    return !!localStorage.getItem('token')
  },

  getUser() {
    const user = localStorage.getItem('user')
    return user ? JSON.parse(user) : null
  }
}
```

#### 3.2 Login Component Example

```vue
<!-- src/components/Login.vue -->
<template>
  <div class="login-form">
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>Email:</label>
        <input
          v-model="loginForm.email"
          type="email"
          required
          placeholder="teacher@example.com"
        />
      </div>

      <div class="form-group">
        <label>Password:</label>
        <input
          v-model="loginForm.password"
          type="password"
          required
          placeholder="••••••••"
        />
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Logging in...' : 'Login' }}
      </button>

      <div v-if="error" class="error">{{ error }}</div>
    </form>
  </div>
</template>

<script>
import authService from '@/services/auth'

export default {
  name: 'Login',
  data() {
    return {
      loginForm: {
        email: '',
        password: ''
      },
      loading: false,
      error: ''
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = ''

      try {
        await authService.login(
          this.loginForm.email,
          this.loginForm.password
        )

        // Redirect to dashboard
        this.$router.push('/dashboard')
      } catch (error) {
        this.error = error.response?.data?.error || 'Login failed'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
```

### 4. File Upload Integration

#### 4.1 Upload Service

```javascript
// src/services/upload.js
import api from './api'

export default {
  async uploadModelAnswer(formData) {
    const response = await api.post('/evaluation-schemes', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async uploadAnswerSheheets(formData) {
    const response = await api.post('/answer-sheets/bulk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
}
```

#### 4.2 File Upload Component Example

```vue
<!-- src/components/ModelAnswerUpload.vue -->
<template>
  <div class="upload-form">
    <form @submit.prevent="handleUpload">
      <div class="form-group">
        <label>Title:</label>
        <input v-model="form.title" type="text" required />
      </div>

      <div class="form-group">
        <label>Subject:</label>
        <input v-model="form.subject" type="text" />
      </div>

      <div class="form-group">
        <label>Total Marks:</label>
        <input v-model="form.totalMarks" type="number" required min="1" />
      </div>

      <div class="form-group">
        <label>Model Answer PDF:</label>
        <input
          type="file"
          ref="fileInput"
          accept=".pdf"
          @change="handleFileChange"
          required
        />
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Uploading...' : 'Upload' }}
      </button>

      <div v-if="message" class="message">{{ message }}</div>
    </form>
  </div>
</template>

<script>
import uploadService from '@/services/upload'

export default {
  name: 'ModelAnswerUpload',
  data() {
    return {
      form: {
        title: '',
        subject: '',
        totalMarks: '',
        modelAnswer: null
      },
      loading: false,
      message: ''
    }
  },
  methods: {
    handleFileChange(event) {
      this.form.modelAnswer = event.target.files[0]
    },

    async handleUpload() {
      this.loading = true
      this.message = ''

      try {
        const formData = new FormData()
        formData.append('title', this.form.title)
        formData.append('subject', this.form.subject)
        formData.append('total_marks', this.form.totalMarks)
        formData.append('model_answer', this.form.modelAnswer)

        const result = await uploadService.uploadModelAnswer(formData)
        this.message = 'Model answer uploaded successfully!'

        // Reset form
        this.form = { title: '', subject: '', totalMarks: '', modelAnswer: null }
        this.$refs.fileInput.value = ''

        // Emit success event
        this.$emit('success', result.scheme)
      } catch (error) {
        this.message = error.response?.data?.error || 'Upload failed'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
```

### 5. API Endpoints Reference

#### Authentication
```javascript
// Login
POST /api/auth/login
{
  "email": "teacher@example.com",
  "password": "password123"
}

// Register
POST /api/auth/register
{
  "email": "teacher@example.com",
  "password": "password123",
  "name": "John Doe"
}

// Get current user
GET /api/auth/me
Headers: Authorization: Bearer <token>
```

#### Evaluation Schemes
```javascript
// Create scheme
POST /api/evaluation-schemes
Headers: Authorization: Bearer <token>
Content-Type: multipart/form-data
Body: FormData with title, subject, total_marks, model_answer (file)

// List schemes
GET /api/evaluation-schemes?page=1&limit=20
Headers: Authorization: Bearer <token>

// Get scheme details
GET /api/evaluation-schemes/:id
Headers: Authorization: Bearer <token>

// Delete scheme
DELETE /api/evaluation-schemes/:id
Headers: Authorization: Bearer <token>
```

#### Answer Sheets
```javascript
// Bulk upload answer sheets
POST /api/answer-sheets/bulk
Headers: Authorization: Bearer <token>
Content-Type: multipart/form-data
Body: FormData with evaluation_scheme_id, answer_sheets (files)

// List answer sheets
GET /api/answer-sheets?evaluation_scheme_id=xxx&status=completed
Headers: Authorization: Bearer <token>

// Get answer sheet details
GET /api/answer-sheets/:id
Headers: Authorization: Bearer <token>
```

### 6. Testing the Connection

#### 6.1 Simple Test
```javascript
// In your Vue component's mounted() method
async mounted() {
  try {
    const response = await this.$axios.get('http://localhost:5000/')
    console.log('Backend connected:', response.data)
  } catch (error) {
    console.error('Backend connection failed:', error)
  }
}
```

#### 6.2 Health Check
```javascript
// Check backend health
async checkBackendHealth() {
  try {
    const response = await api.get('/health')
    console.log('Backend health:', response.data)
    return response.data
  } catch (error) {
    console.error('Backend health check failed:', error)
    return null
  }
}
```

### 7. Troubleshooting

#### Common Issues:

1. **CORS Errors:**
   - Make sure `FRONTEND_URL` in `.env` matches your frontend URL
   - Check that the backend is running before the frontend

2. **401 Unauthorized:**
   - Ensure JWT token is being sent in Authorization header
   - Check token hasn't expired (7 days by default)

3. **File Upload Issues:**
   - Ensure `Content-Type: multipart/form-data` is set
   - Check file size is under 10MB limit
   - Verify files are PDF format

4. **MongoDB Connection:**
   - Ensure MongoDB is running
   - Check MONGODB_URI in `.env` is correct
   - Create the database if it doesn't exist

5. **OpenAI API Issues:**
   - Verify OPENAI_API_KEY is valid
   - Check you have sufficient API credits

### 8. Production Deployment

For production deployment:

1. **Backend:**
   - Set `FLASK_ENV=production`
   - Use a production WSGI server (Gunicorn)
   - Configure HTTPS
   - Use environment variables for secrets

2. **Frontend:**
   - Update API_BASE_URL to production URL
   - Configure proper CORS origins
   - Build optimized bundle

Your backend is now ready for frontend integration! 🚀