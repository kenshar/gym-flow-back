import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

import sequelize from './db/index.js';
import './models/index.js';

import authRoutes from './routes/auth.routes.js';
import memberRoutes from './routes/members.routes.js';
import attendanceRoutes from './routes/attendance.routes.js';
import workoutRoutes from './routes/workouts.routes.js';
import reportRoutes from './routes/reports.routes.js';
import { errorHandler } from './middleware/error.middleware.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/members', memberRoutes);
app.use('/api/attendance', attendanceRoutes);
app.use('/api/workouts', workoutRoutes);
app.use('/api/reports', reportRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use(errorHandler);

// Database connection and server start
sequelize
  .authenticate()
  .then(() => {
    console.log('Connected to PostgreSQL');
    return sequelize.sync();
  })
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error('Database connection error:', err);
    process.exit(1);
  });
