import { DataTypes } from 'sequelize';
import sequelize from '../db/index.js';

const Attendance = sequelize.define(
  'Attendance',
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true,
    },
    memberId: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: 'Members',
        key: 'id',
      },
    },
    userId: {
      type: DataTypes.UUID,
      references: {
        model: 'Users',
        key: 'id',
      },
    },
    checkInTime: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
    },
    checkOutTime: {
      type: DataTypes.DATE,
    },
    duration: {
      type: DataTypes.INTEGER, // in minutes
    },
    notes: {
      type: DataTypes.STRING(200),
    },
  },
  {
    timestamps: true,
    indexes: [
      {
        fields: ['checkInTime'],
      },
      {
        fields: ['memberId', 'checkInTime'],
      },
    ],
    hooks: {
      beforeSave: (attendance) => {
        if (attendance.checkOutTime && attendance.checkInTime) {
          const diffMs = new Date(attendance.checkOutTime) - new Date(attendance.checkInTime);
          attendance.duration = Math.round(diffMs / (1000 * 60));
        }
      },
    },
  }
);

export default Attendance;
