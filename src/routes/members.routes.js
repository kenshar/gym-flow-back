import express from 'express';
import { Op } from 'sequelize';
import { Member, Attendance, Workout } from '../models/index.js';
import { authenticate, authorize } from '../middleware/auth.middleware.js';

const router = express.Router();

// Get all members (with filtering and search)
router.get('/', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const { search, status, membershipType, page = 1, limit = 20 } = req.query;

    const where = {};

    if (search) {
      where[Op.or] = [
        { name: { [Op.iLike]: `%${search}%` } },
        { email: { [Op.iLike]: `%${search}%` } },
      ];
    }

    if (status && status !== 'all') {
      where.membershipStatus = status;
    }

    if (membershipType && membershipType !== 'all') {
      where.membershipType = membershipType;
    }

    const offset = (page - 1) * limit;

    const { rows: members, count: total } = await Member.findAndCountAll({
      where,
      order: [['createdAt', 'DESC']],
      offset,
      limit: parseInt(limit),
    });

    res.json({
      members,
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

// Get single member
router.get('/:id', authenticate, async (req, res, next) => {
  try {
    const member = await Member.findByPk(req.params.id);
    if (!member) {
      return res.status(404).json({ message: 'Member not found' });
    }
    res.json(member);
  } catch (error) {
    next(error);
  }
});

// Get member stats
router.get('/:id/stats', authenticate, async (req, res, next) => {
  try {
    const memberId = req.params.id;

    const [attendanceCount, workoutCount, recentAttendance, recentWorkouts, attendanceWithDuration] =
      await Promise.all([
        Attendance.count({ where: { memberId } }),
        Workout.count({ where: { memberId } }),
        Attendance.findAll({
          where: { memberId },
          order: [['checkInTime', 'DESC']],
          limit: 5,
        }),
        Workout.findAll({
          where: { memberId },
          order: [['date', 'DESC']],
          limit: 5,
        }),
        Attendance.findAll({
          where: {
            memberId,
            duration: { [Op.ne]: null },
          },
        }),
      ]);

    const avgDuration =
      attendanceWithDuration.length > 0
        ? attendanceWithDuration.reduce((sum, a) => sum + a.duration, 0) / attendanceWithDuration.length
        : 0;

    res.json({
      totalVisits: attendanceCount,
      totalWorkouts: workoutCount,
      averageVisitDuration: Math.round(avgDuration),
      recentAttendance,
      recentWorkouts,
    });
  } catch (error) {
    next(error);
  }
});

// Create member
router.post('/', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const member = await Member.create(req.body);
    res.status(201).json(member);
  } catch (error) {
    next(error);
  }
});

// Update member
router.put('/:id', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const member = await Member.findByPk(req.params.id);

    if (!member) {
      return res.status(404).json({ message: 'Member not found' });
    }

    await member.update(req.body);
    res.json(member);
  } catch (error) {
    next(error);
  }
});

// Delete member
router.delete('/:id', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const member = await Member.findByPk(req.params.id);

    if (!member) {
      return res.status(404).json({ message: 'Member not found' });
    }

    await member.destroy();
    res.json({ message: 'Member deleted successfully' });
  } catch (error) {
    next(error);
  }
});

export default router;
