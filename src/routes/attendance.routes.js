import express from 'express';
import { Op } from 'sequelize';
import { Attendance, Member } from '../models/index.js';
import { authenticate, authorize } from '../middleware/auth.middleware.js';

const router = express.Router();

// Get attendance records
router.get('/', authenticate, async (req, res, next) => {
  try {
    const { memberId, startDate, endDate, page = 1, limit = 20 } = req.query;

    const where = {};

    if (memberId) {
      where.memberId = memberId;
    }

    if (startDate || endDate) {
      where.checkInTime = {};
      if (startDate) where.checkInTime[Op.gte] = new Date(startDate);
      if (endDate) where.checkInTime[Op.lte] = new Date(endDate);
    }

    const offset = (page - 1) * limit;

    const { rows: records, count: total } = await Attendance.findAndCountAll({
      where,
      include: [{ model: Member, as: 'member', attributes: ['name', 'email'] }],
      order: [['checkInTime', 'DESC']],
      offset,
      limit: parseInt(limit),
    });

    res.json({
      records,
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

// Get today's attendance
router.get('/today', authenticate, async (req, res, next) => {
  try {
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const endOfDay = new Date();
    endOfDay.setHours(23, 59, 59, 999);

    const records = await Attendance.findAll({
      where: {
        checkInTime: { [Op.between]: [startOfDay, endOfDay] },
      },
      include: [{ model: Member, as: 'member', attributes: ['name', 'email'] }],
      order: [['checkInTime', 'DESC']],
    });

    res.json(records);
  } catch (error) {
    next(error);
  }
});

// Get attendance stats
router.get('/stats', authenticate, async (req, res, next) => {
  try {
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const startOfWeek = new Date();
    startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());
    startOfWeek.setHours(0, 0, 0, 0);

    const startOfMonth = new Date();
    startOfMonth.setDate(1);
    startOfMonth.setHours(0, 0, 0, 0);

    const [todayCount, weekCount, monthCount, currentlyCheckedIn] = await Promise.all([
      Attendance.count({ where: { checkInTime: { [Op.gte]: startOfDay } } }),
      Attendance.count({ where: { checkInTime: { [Op.gte]: startOfWeek } } }),
      Attendance.count({ where: { checkInTime: { [Op.gte]: startOfMonth } } }),
      Attendance.count({
        where: {
          checkInTime: { [Op.gte]: startOfDay },
          checkOutTime: null,
        },
      }),
    ]);

    res.json({
      today: todayCount,
      thisWeek: weekCount,
      thisMonth: monthCount,
      currentlyCheckedIn,
    });
  } catch (error) {
    next(error);
  }
});

// Check in
router.post('/check-in', authenticate, async (req, res, next) => {
  try {
    const { memberId, notes } = req.body;

    // Verify member exists and is active
    const member = await Member.findByPk(memberId);
    if (!member) {
      return res.status(404).json({ message: 'Member not found' });
    }

    if (member.membershipStatus !== 'active') {
      return res.status(400).json({ message: 'Member membership is not active' });
    }

    // Check if already checked in today
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const existingCheckIn = await Attendance.findOne({
      where: {
        memberId,
        checkInTime: { [Op.gte]: startOfDay },
        checkOutTime: null,
      },
    });

    if (existingCheckIn) {
      return res.status(400).json({ message: 'Member is already checked in' });
    }

    const attendance = await Attendance.create({
      memberId,
      userId: req.user.id,
      notes,
    });

    res.status(201).json(attendance);
  } catch (error) {
    next(error);
  }
});

// Check out
router.post('/check-out', authenticate, async (req, res, next) => {
  try {
    const { memberId } = req.body;

    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const attendance = await Attendance.findOne({
      where: {
        memberId,
        checkInTime: { [Op.gte]: startOfDay },
        checkOutTime: null,
      },
    });

    if (!attendance) {
      return res.status(404).json({ message: 'No active check-in found for today' });
    }

    attendance.checkOutTime = new Date();
    await attendance.save();

    res.json(attendance);
  } catch (error) {
    next(error);
  }
});

export default router;
