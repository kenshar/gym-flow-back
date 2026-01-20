import express from 'express';
import { Op } from 'sequelize';
import { Workout } from '../models/index.js';
import { authenticate } from '../middleware/auth.middleware.js';

const router = express.Router();

// Get workout types
router.get('/types', authenticate, async (req, res) => {
  const types = [
    { name: 'Strength Training', icon: 'dumbbell' },
    { name: 'Cardio', icon: 'heart' },
    { name: 'HIIT', icon: 'fire' },
    { name: 'Yoga', icon: 'spa' },
    { name: 'Pilates', icon: 'accessibility' },
    { name: 'Swimming', icon: 'pool' },
    { name: 'CrossFit', icon: 'fitness' },
    { name: 'Other', icon: 'more' },
  ];
  res.json(types);
});

// Get workouts
router.get('/', authenticate, async (req, res, next) => {
  try {
    const { type, startDate, endDate, page = 1, limit = 20 } = req.query;

    const where = { userId: req.user.id };

    if (type) {
      where.type = type;
    }

    if (startDate || endDate) {
      where.date = {};
      if (startDate) where.date[Op.gte] = new Date(startDate);
      if (endDate) where.date[Op.lte] = new Date(endDate);
    }

    const offset = (page - 1) * limit;

    const { rows: workouts, count: total } = await Workout.findAndCountAll({
      where,
      order: [['date', 'DESC']],
      offset,
      limit: parseInt(limit),
    });

    res.json({
      workouts,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    next(error);
  }
});

// Get single workout
router.get('/:id', authenticate, async (req, res, next) => {
  try {
    const workout = await Workout.findOne({
      where: { id: req.params.id, userId: req.user.id },
    });

    if (!workout) {
      return res.status(404).json({ message: 'Workout not found' });
    }

    res.json(workout);
  } catch (error) {
    next(error);
  }
});

// Create workout
router.post('/', authenticate, async (req, res, next) => {
  try {
    const { type, name, duration, calories, intensity, exercises, notes, date } = req.body;

    // Server-side validation and type conversion
    const workoutData = {
      userId: req.user.id,
      type,
      name,
      duration: parseInt(duration, 10) || 0,
      calories: parseInt(calories, 10) || 0,
      intensity,
      exercises,
      notes,
      date: date ? new Date(date) : new Date(),
    };

    if (workoutData.duration < 1) {
      return res.status(400).json({ message: 'Duration must be at least 1 minute' });
    }

    const workout = await Workout.create(workoutData);
    res.status(201).json(workout);
  } catch (error) {
    next(error);
  }
});

// Update workout
router.put('/:id', authenticate, async (req, res, next) => {
  try {
    const workout = await Workout.findOne({
      where: { id: req.params.id, userId: req.user.id },
    });

    if (!workout) {
      return res.status(404).json({ message: 'Workout not found' });
    }

    const { type, name, duration, calories, intensity, exercises, notes, date } = req.body;

    const updateData = {};
    if (type !== undefined) updateData.type = type;
    if (name !== undefined) updateData.name = name;
    if (duration !== undefined) updateData.duration = parseInt(duration, 10);
    if (calories !== undefined) updateData.calories = parseInt(calories, 10);
    if (intensity !== undefined) updateData.intensity = intensity;
    if (exercises !== undefined) updateData.exercises = exercises;
    if (notes !== undefined) updateData.notes = notes;
    if (date !== undefined) updateData.date = new Date(date);

    await workout.update(updateData);
    res.json(workout);
  } catch (error) {
    next(error);
  }
});

// Delete workout
router.delete('/:id', authenticate, async (req, res, next) => {
  try {
    const workout = await Workout.findOne({
      where: { id: req.params.id, userId: req.user.id },
    });

    if (!workout) {
      return res.status(404).json({ message: 'Workout not found' });
    }

    await workout.destroy();
    res.json({ message: 'Workout deleted successfully' });
  } catch (error) {
    next(error);
  }
});

export default router;
