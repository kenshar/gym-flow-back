import User from './User.model.js';
import Member from './Member.model.js';
import Attendance from './Attendance.model.js';
import Workout from './Workout.model.js';

// Define associations
User.hasOne(Member, { foreignKey: 'userId', as: 'member' });
Member.belongsTo(User, { foreignKey: 'userId', as: 'user' });

Member.hasMany(Attendance, { foreignKey: 'memberId', as: 'attendances' });
Attendance.belongsTo(Member, { foreignKey: 'memberId', as: 'member' });

User.hasMany(Attendance, { foreignKey: 'userId', as: 'recordedAttendances' });
Attendance.belongsTo(User, { foreignKey: 'userId', as: 'recordedBy' });

User.hasMany(Workout, { foreignKey: 'userId', as: 'workouts' });
Workout.belongsTo(User, { foreignKey: 'userId', as: 'user' });

Member.hasMany(Workout, { foreignKey: 'memberId', as: 'workouts' });
Workout.belongsTo(Member, { foreignKey: 'memberId', as: 'member' });

export { User, Member, Attendance, Workout };
