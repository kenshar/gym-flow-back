import { DataTypes } from 'sequelize';
import sequelize from '../db/index.js';

const Workout = sequelize.define(
  'Workout',
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true,
    },
    userId: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: 'Users',
        key: 'id',
      },
    },
    memberId: {
      type: DataTypes.UUID,
      references: {
        model: 'Members',
        key: 'id',
      },
    },
    type: {
      type: DataTypes.ENUM(
        'Strength Training',
        'Cardio',
        'HIIT',
        'Yoga',
        'Pilates',
        'Swimming',
        'CrossFit',
        'Other'
      ),
      allowNull: false,
    },
    name: {
      type: DataTypes.STRING(100),
    },
    duration: {
      type: DataTypes.INTEGER, // in minutes
      allowNull: false,
      validate: {
        min: { args: [1], msg: 'Duration must be at least 1 minute' },
      },
    },
    calories: {
      type: DataTypes.INTEGER,
      validate: {
        min: { args: [0], msg: 'Calories cannot be negative' },
      },
    },
    intensity: {
      type: DataTypes.ENUM('low', 'medium', 'high'),
      defaultValue: 'medium',
    },
    exercises: {
      type: DataTypes.JSONB,
      defaultValue: [],
    },
    notes: {
      type: DataTypes.STRING(500),
    },
    date: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW,
    },
  },
  {
    timestamps: true,
    indexes: [
      {
        fields: ['userId', 'date'],
      },
    ],
  }
);

export default Workout;
