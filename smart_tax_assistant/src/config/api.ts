// API Configuration
export const API_CONFIG = {
  // Tax Advisor Backend API
  TAX_ADVISOR_BASE_URL: process.env.NEXT_PUBLIC_TAX_ADVISOR_API_URL || 'http://localhost:8000',

  // API Endpoints
  ENDPOINTS: {
    CALCULATE_TAX: '/api/calculate-tax',
  }
};

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.TAX_ADVISOR_BASE_URL}${endpoint}`;
};
