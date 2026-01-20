import { DataTypes } from 'sequelize';
import sequelize from '../db/index.js';

const Member = sequelize.define(
  'Member',
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true,
    },
    userId: {
      type: DataTypes.UUID,
      references: {
        model: 'Users',
        key: 'id',
      },
    },
    name: {
      type: DataTypes.STRING(100),
      allowNull: false,
      validate: {
        notEmpty: { msg: 'Name is required' },
      },
    },
    email: {
      type: DataTypes.STRING(255),
      allowNull: false,
      unique: true,
      validate: {
        isEmail: { msg: 'Please provide a valid email' },
      },
    },
    phone: {
      type: DataTypes.STRING(20),
    },
    membershipType: {
      type: DataTypes.ENUM('basic', 'premium', 'vip'),
      defaultValue: 'basic',
    },
    membershipStatus: {
      type: DataTypes.ENUM('active', 'inactive', 'expired', 'suspended'),
      defaultValue: 'active',
    },
    membershipStartDate: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW,
    },
    membershipEndDate: {
      type: DataTypes.DATE,
    },
    emergencyContactName: {
      type: DataTypes.STRING(100),
    },
    emergencyContactPhone: {
      type: DataTypes.STRING(20),
    },
    emergencyContactRelationship: {
      type: DataTypes.STRING(50),
    },
    notes: {
      type: DataTypes.STRING(500),
    },
  },
  {
    timestamps: true,
    indexes: [
      {
        fields: ['name'],
      },
      {
        fields: ['email'],
      },
      {
        fields: ['membershipStatus'],
      },
    ],
  }
);

export default Member;
