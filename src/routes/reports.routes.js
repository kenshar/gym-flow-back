import express from 'express';
import { Op, fn, col, literal } from 'sequelize';
import sequelize from '../db/index.js';
import { Member, Attendance, Workout, User } from '../models/index.js';
import { authenticate, authorize } from '../middleware/auth.middleware.js';

const router = express.Router();

// Get summary report
router.get('/summary', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const { startDate, endDate } = req.query;

    const dateFilter = {};
    if (startDate) dateFilter[Op.gte] = new Date(startDate);
    if (endDate) dateFilter[Op.lte] = new Date(endDate);

    const attendanceWhere = startDate || endDate ? { checkInTime: dateFilter } : {};
    const workoutWhere = startDate || endDate ? { date: dateFilter } : {};

    const [totalMembers, activeMembers, totalAttendance, totalWorkouts] = await Promise.all([
      Member.count(),
      Member.count({ where: { membershipStatus: 'active' } }),
      Attendance.count({ where: attendanceWhere }),
      Workout.count({ where: workoutWhere }),
    ]);

    // Membership breakdown
    const membershipBreakdown = await Member.findAll({
      attributes: ['membershipType', [fn('COUNT', col('id')), 'count']],
      group: ['membershipType'],
      raw: true,
    });

    // Status breakdown
    const statusBreakdown = await Member.findAll({
      attributes: ['membershipStatus', [fn('COUNT', col('id')), 'count']],
      group: ['membershipStatus'],
      raw: true,
    });

    res.json({
      totalMembers,
      activeMembers,
      totalAttendance,
      totalWorkouts,
      membershipBreakdown: membershipBreakdown.reduce((acc, item) => {
        acc[item.membershipType] = parseInt(item.count);
        return acc;
      }, {}),
      statusBreakdown: statusBreakdown.reduce((acc, item) => {
        acc[item.membershipStatus] = parseInt(item.count);
        return acc;
      }, {}),
    });
  } catch (error) {
    next(error);
  }
});

// Get attendance report
router.get('/attendance', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const { startDate, endDate, groupBy = 'day' } = req.query;

    const where = {};
    if (startDate || endDate) {
      where.checkInTime = {};
      if (startDate) where.checkInTime[Op.gte] = new Date(startDate);
      if (endDate) where.checkInTime[Op.lte] = new Date(endDate);
    }

    let dateFormat;
    switch (groupBy) {
      case 'week':
        dateFormat = "TO_CHAR(\"checkInTime\", 'IYYY-IW')";
        break;
      case 'month':
        dateFormat = "TO_CHAR(\"checkInTime\", 'YYYY-MM')";
        break;
      default:
        dateFormat = "TO_CHAR(\"checkInTime\", 'YYYY-MM-DD')";
    }

    const data = await Attendance.findAll({
      attributes: [
        [literal(dateFormat), 'period'],
        [fn('COUNT', col('id')), 'count'],
        [fn('AVG', col('duration')), 'avgDuration'],
      ],
      where,
      group: [literal(dateFormat)],
      order: [[literal(dateFormat), 'ASC']],
      raw: true,
    });

    res.json({ data, groupBy });
  } catch (error) {
    next(error);
  }
});

// Get membership report
router.get('/membership', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    // New members over time
    const newMembersOverTime = await Member.findAll({
      attributes: [
        [literal("TO_CHAR(\"createdAt\", 'YYYY-MM')"), 'period'],
        [fn('COUNT', col('id')), 'count'],
      ],
      group: [literal("TO_CHAR(\"createdAt\", 'YYYY-MM')")],
      order: [[literal("TO_CHAR(\"createdAt\", 'YYYY-MM')"), 'ASC']],
      limit: 12,
      raw: true,
    });

    // Expiring memberships (next 30 days)
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

    const expiringMemberships = await Member.findAll({
      where: {
        membershipEndDate: {
          [Op.lte]: thirtyDaysFromNow,
          [Op.gte]: new Date(),
        },
        membershipStatus: 'active',
      },
      attributes: ['name', 'email', 'membershipEndDate', 'membershipType'],
    });

    res.json({
      newMembersOverTime,
      expiringMemberships,
    });
  } catch (error) {
    next(error);
  }
});

// Get revenue report
router.get('/revenue', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const membershipPrices = {
      basic: 29.99,
      premium: 49.99,
      vip: 99.99,
    };

    const memberCounts = await Member.findAll({
      attributes: ['membershipType', [fn('COUNT', col('id')), 'count']],
      where: { membershipStatus: 'active' },
      group: ['membershipType'],
      raw: true,
    });

    const estimatedMonthlyRevenue = memberCounts.reduce((total, item) => {
      return total + (membershipPrices[item.membershipType] || 0) * parseInt(item.count);
    }, 0);

    res.json({
      estimatedMonthlyRevenue,
      breakdown: memberCounts.map((item) => ({
        type: item.membershipType,
        count: parseInt(item.count),
        revenue: (membershipPrices[item.membershipType] || 0) * parseInt(item.count),
      })),
    });
  } catch (error) {
    next(error);
  }
});

// Export report
router.get('/export/:type', authenticate, authorize('admin'), async (req, res, next) => {
  try {
    const { type } = req.params;
    const { format = 'json' } = req.query;

    let data;

    switch (type) {
      case 'members':
        data = await Member.findAll({ raw: true });
        break;
      case 'attendance':
        data = await Attendance.findAll({
          include: [{ model: Member, as: 'member', attributes: ['name', 'email'] }],
          raw: true,
          nest: true,
        });
        break;
      case 'workouts':
        data = await Workout.findAll({
          include: [{ model: User, as: 'user', attributes: ['name', 'email'] }],
          raw: true,
          nest: true,
        });
        break;
      default:
        return res.status(400).json({ message: 'Invalid export type' });
    }

    if (format === 'csv') {
      if (data.length === 0) {
        return res.status(404).json({ message: 'No data to export' });
      }

      const flattenObject = (obj, prefix = '') => {
        return Object.keys(obj).reduce((acc, key) => {
          const newKey = prefix ? `${prefix}_${key}` : key;
          if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
            Object.assign(acc, flattenObject(obj[key], newKey));
          } else {
            acc[newKey] = obj[key];
          }
          return acc;
        }, {});
      };

      const flatData = data.map((item) => flattenObject(item));
      const headers = Object.keys(flatData[0]).join(',');
      const rows = flatData.map((item) =>
        Object.values(item)
          .map((val) => (val === null ? '' : typeof val === 'string' ? `"${val}"` : val))
          .join(',')
      );

      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename=${type}-export.csv`);
      return res.send([headers, ...rows].join('\n'));
    }

    res.json({ data, count: data.length });
  } catch (error) {
    next(error);
  }
});

export default router;
