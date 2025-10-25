// Water Management System
class WaterSystem {
    constructor() {
        this.maxWater = 2000; // Maximum water capacity in liters
        this.currentWater = 0; // Will be set from server
        this.waterElement = null;
        this.waterInfoElement = null;
        this.init();
    }

    init() {
        this.createWaterBackground();
        this.fetchCurrentWaterLevel();
        
        // Update water level every 5 seconds
        setInterval(() => {
            this.fetchCurrentWaterLevel();
        }, 5000);
    }

    createWaterBackground() {
        // Create water background container
        const waterBg = document.createElement('div');
        waterBg.className = 'water-background';
        
        // Create water level element
        const waterLevel = document.createElement('div');
        waterLevel.className = 'water-level';
        waterLevel.innerHTML = `
            <div class="water-wave"></div>
            <div class="water-wave"></div>
        `;
        
        waterBg.appendChild(waterLevel);
        document.body.appendChild(waterBg);
        
        this.waterElement = waterLevel;
    }

    async fetchCurrentWaterLevel() {
        try {
            const response = await fetch('/api/water-level');
            if (response.ok) {
                const data = await response.json();
                this.updateWaterLevel(data.water_level, false);
            }
        } catch (error) {
            console.log('Could not fetch water level:', error);
        }
    }

    async depleteWater() {
        try {
            const response = await fetch('/api/deplete-water', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateWaterLevel(data.water_level, true);
                return data;
            }
        } catch (error) {
            console.error('Error depleting water:', error);
        }
        return null;
    }

    updateWaterLevel(newLevel, animate = true) {
        this.currentWater = newLevel;
        const percentage = (newLevel / this.maxWater) * 100;
        
        // Update background water level
        if (this.waterElement) {
            this.waterElement.style.height = `${percentage}%`;
        }
    }
}

// Global water system instance
let waterSystem;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    waterSystem = new WaterSystem();
});

// Make depleteWater available globally for chatbot
window.depleteWater = function() {
    if (waterSystem) {
        return waterSystem.depleteWater();
    }
    return null;
};