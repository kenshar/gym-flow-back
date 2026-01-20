import sequelize from './index.js';
import '../models/index.js';

async function syncDatabase() {
  try {
    await sequelize.authenticate();
    console.log('Database connection established.');

    await sequelize.sync({ alter: true });
    console.log('Database synchronized.');

    process.exit(0);
  } catch (error) {
    console.error('Database sync failed:', error);
    process.exit(1);
  }
}

syncDatabase();
