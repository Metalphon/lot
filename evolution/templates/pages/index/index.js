const MAX_SAFE_NUMBER = 1e308;  // 设置安全的最大数值

// 添加数值限制函数
function limitNumber(num) {
  if (typeof num !== 'number' || isNaN(num)) return 0;
  if (num > MAX_SAFE_NUMBER) return MAX_SAFE_NUMBER;
  if (num < 0) return 0;
  return Math.floor(num);
}

Page({
  data: {
    currentSystem: 'biology',
    gameState: {
      // 基础资源
      particles: 10,
      nuclei: 0,
      atoms: 0,
      molecules: 0,
      proteins: 0,
      membrane: 0,
      cells: 0,
      organisms: 0,
      worms: 0,
      fish: 0,
      animals: 0,
      mammals: 0,
      apes: 0,
      humans: 0,
      
      // 栖息地资源
      stone: 0,
      mountain: 0,
      continent: 0,
      planet: 0,
      star: 0,
      galaxy: 0,
      cluster: 0,
      blackhole: 0,
      territory: 0,
      
      // 自动购买状态 - 修正键名
      autoNucleus: false,
      autoAtoms: false,
      autoMolecules: false,
      autoProteins: false,
      autoMembrane: false,
      autoCells: false,
      autoOrganisms: false,
      autoWorms: false,
      autoFish: false,
      autoAnimals: false,
      autoMammals: false,
      autoApes: false,
      autoHumans: false,
      
      // 栖息地自动购买状态
      autoStone: false,
      autoMountain: false,
      autoContinent: false,
      autoPlanet: false,
      autoStar: false,
      autoGalaxy: false,
      autoCluster: false,
      autoBlackhole: false,
      
      // 进化计数
      evolutionCounts: {
        nuclei: 0,
        atoms: 0,
        molecules: 0,
        proteins: 0,
        membrane: 0,
        cells: 0,
        organisms: 0,
        worms: 0,
        fish: 0,
        animals: 0,
        mammals: 0,
        apes: 0,
        humans: 0
      }
    },

    // 生产率基数
    productionRates: {
      particles: 1,
      nuclei: 1,
      atoms: 2,
      molecules: 3,
      proteins: 4,
      membrane: 5,
      cells: 6,
      organisms: 8,
      worms: 10,
      fish: 12,
      animals: 15,
      mammals: 20,
      apes: 25,
      humans: 30,
      stone: 5,
      mountain: 10,
      continent: 20,
      planet: 40,
      star: 80,
      galaxy: 160,
      cluster: 320,
      blackhole: 640
    },

    // 价格配置（调整为更合理的增长曲线）
    prices: {
      nuclei: 10,
      atoms: 50,
      molecules: 250,
      proteins: 1000,
      membrane: 5000,
      cells: 25000,
      organisms: 100000,
      worms: 500000,
      fish: 2500000,
      animals: 10000000,
      mammals: 50000000,
      apes: 250000000,
      humans: 1000000000,
      stone: 100,
      mountain: 1000,
      continent: 10000,
      planet: 100000,
      star: 1000000,
      galaxy: 10000000,
      cluster: 100000000,
      blackhole: 1000000000
    },

    // 生物资源配置
    biologicalResources: [
      { name: '原子', key: 'atoms', class: 'atom', currency: '原子核' },
      { name: '分子', key: 'molecules', class: 'molecule', currency: '原子' },
      { name: '蛋白质', key: 'proteins', class: 'protein', currency: '分子' },
      { name: '细胞膜', key: 'membrane', class: 'membrane', currency: '蛋白质' },
      { name: '细胞', key: 'cells', class: 'cell', currency: '细胞膜' },
      { name: '微生物', key: 'organisms', class: 'organism', currency: '细胞' },
      { name: '蠕虫', key: 'worms', class: 'worm', currency: '微生物' },
      { name: '鱼类', key: 'fish', class: 'fish', currency: '蠕虫' },
      { name: '动物', key: 'animals', class: 'animal', currency: '鱼类' },
      { name: '哺乳动物', key: 'mammals', class: 'mammal', currency: '动物' },
      { name: '灵长类', key: 'apes', class: 'ape', currency: '哺乳动物' },
      { name: '智慧生命', key: 'humans', class: 'human', currency: '灵长类' }
    ],

    // 栖息地资源配置
    habitatResources: [
      { name: '石头', key: 'stone', class: 'stone' },
      { name: '山脉', key: 'mountain', class: 'mountain' },
      { name: '大陆', key: 'continent', class: 'continent' },
      { name: '行星', key: 'planet', class: 'planet' },
      { name: '恒星', key: 'star', class: 'star' },
      { name: '星系', key: 'galaxy', class: 'galaxy' },
      { name: '星系团', key: 'cluster', class: 'cluster' },
      { name: '黑洞', key: 'blackhole', class: 'blackhole' }
    ],

    // 显示数据
    displayData: {},
    
    // 进化状态
    canEvolve: {}
  },

  onLoad() {
    // 立即执行一次更新
    this.updateProduction();
    this.updateDisplay();
    
    // 启动游戏循环，每1秒更新一次
    this.gameLoopInterval = setInterval(() => {
      this.updateProduction();
      this.updateHabitatProduction();
      this.autoBuy();
      this.updateDisplay();
    }, 1000);  // 改回1000ms
  },

  onUnload() {
    if (this.gameLoopInterval) {
      clearInterval(this.gameLoopInterval);
    }
  },

  // 切换系统
  switchSystem(e) {
    const system = e.currentTarget.dataset.system;
    this.setData({
      currentSystem: system
    });
  },

  // 购买资源
  buyResource(e) {
    const resource = e.currentTarget.dataset.resource;
    const price = this.getCurrentPrice(resource);
    const currency = this.getResourceCurrency(resource);
    
    // 调试日志
    console.log('尝试购买:', {
      resource,
      price,
      currency,
      available: this.data.gameState[currency]
    });
    
    if (this.data.gameState[currency] >= price) {
      const gameState = this.data.gameState;
      gameState[currency] -= price;
      gameState[resource] += 1;
      
      this.setData({ gameState });
      this.updateDisplay();
    }
  },

  // 购买栖息地
  buyHabitat(e) {
    const resource = e.currentTarget.dataset.resource;
    const price = this.getCurrentPrice(resource);
    
    if (this.data.gameState.particles >= price) {
      const gameState = this.data.gameState;
      gameState.particles -= price;
      gameState[resource] += 1;
      
      this.setData({ gameState });
      this.updateDisplay();
    }
  },

  // 添加强制刷新UI的函数
  forceRefreshUI() {
    // 创建一个临时变量触发视图更新
    this.setData({ _timestamp: Date.now() });
    
    // 对gameState进行深拷贝并重新设置，强制更新视图
    const gameStateCopy = JSON.parse(JSON.stringify(this.data.gameState));
    this.setData({ gameState: gameStateCopy });
    
    // 确保按钮的CSS规则被重新应用
    setTimeout(() => {
      this.setData({ _refresh: Math.random() });
    }, 100);
  },

  // 切换自动购买
  toggleAuto(e) {
    try {
      const resource = e.currentTarget.dataset.resource;
      console.log('切换自动购买，资源:', resource);
      
      // 特殊处理原子核
      if (resource === 'nucleus') {
        // 直接反转状态
        const autoKey = 'autoNucleus';
        const currentValue = !!this.data.gameState[autoKey];
        const newValue = !currentValue;
        
        console.log(`${autoKey}: ${currentValue} -> ${newValue}`);
        
        // 创建新的gameState对象
        const newGameState = {...this.data.gameState, [autoKey]: newValue};
        
        // 立即更新UI
        this.setData({
          gameState: newGameState
        });
        
        // 强制刷新UI
        this.forceRefreshUI();
        
        // 如果启用了自动购买，立即进行一次购买
        if (newValue) {
          setTimeout(() => this.autoBuy(), 50);
        }
        return;
      }
      
      // 其他资源的处理
      const autoKey = 'auto' + resource.charAt(0).toUpperCase() + resource.slice(1);
      
      if (autoKey in this.data.gameState) {
        // 直接反转状态
        const currentValue = !!this.data.gameState[autoKey]; 
        const newValue = !currentValue;
        
        console.log(`${autoKey}: ${currentValue} -> ${newValue}`);
        
        // 创建新的gameState对象并立即更新
        const newGameState = {...this.data.gameState};
        newGameState[autoKey] = newValue;
        
        this.setData({
          gameState: newGameState
        });
        
        // 强制刷新UI
        this.forceRefreshUI();
        
        // 如果启用了自动购买，立即进行一次购买
        if (newValue) {
          setTimeout(() => this.autoBuy(), 50);
        }
      } else {
        console.error('自动购买键名不存在:', autoKey);
      }
    } catch (error) {
      console.error('切换自动购买出错:', error);
    }
  },

  // 切换栖息地自动购买
  toggleAutoHabitat(e) {
    try {
      const resource = e.currentTarget.dataset.resource;
      console.log('切换栖息地自动购买，资源:', resource);
      
      const autoKey = 'auto' + resource.charAt(0).toUpperCase() + resource.slice(1);
      
      if (autoKey in this.data.gameState) {
        // 直接反转状态
        const currentValue = !!this.data.gameState[autoKey];
        const newValue = !currentValue;
        
        console.log(`${autoKey}: ${currentValue} -> ${newValue}`);
        
        // 创建新的gameState对象并立即更新
        const newGameState = {...this.data.gameState};
        newGameState[autoKey] = newValue;
        
        this.setData({
          gameState: newGameState
        });
        
        // 强制刷新UI
        this.forceRefreshUI();
        
        // 如果启用了自动购买，立即进行一次购买
        if (newValue) {
          setTimeout(() => this.autoBuy(), 50);
        }
      } else {
        console.error('自动购买键名不存在:', autoKey);
      }
    } catch (error) {
      console.error('切换栖息地自动购买出错:', error);
    }
  },

  // 进化资源
  evolveResource(e) {
    const resource = e.currentTarget.dataset.resource;
    if (this.data.canEvolve[resource]) {
      const gameState = this.data.gameState;
      gameState.evolutionCounts[resource]++;
      gameState.territory -= this.getEvolutionCost(resource);
      
      this.setData({ gameState });
      this.updateDisplay();
    }
  },

  // 时间加速
  skipTime() {
    for (let i = 0; i < 100; i++) {
      this.updateProduction();
      this.updateHabitatProduction();
    }
    this.updateDisplay();
  },

  // 更新生产
  updateProduction() {
    const gameState = this.data.gameState;
    let changed = false;

    try {
      // 从高到低计算生产（生物系统）
      if (gameState.humans > 0) {
        const efficiency = this.calculateEfficiency(gameState.humans);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.humans) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.humans) || 1;
        
        const apeProduction = limitNumber(gameState.humans * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.humans * baseRate * efficiency * evolutionMultiplier * 2);
        
        if (apeProduction > 0 || particleProduction > 0) {
          gameState.apes = limitNumber((Number(gameState.apes) || 0) + apeProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.apes > 0) {
        const efficiency = this.calculateEfficiency(gameState.apes);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.apes) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.apes) || 1;
        
        const mammalProduction = limitNumber(gameState.apes * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.apes * baseRate * efficiency * evolutionMultiplier * 1.8);
        
        if (mammalProduction > 0 || particleProduction > 0) {
          gameState.mammals = limitNumber((Number(gameState.mammals) || 0) + mammalProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.mammals > 0) {
        const efficiency = this.calculateEfficiency(gameState.mammals);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.mammals) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.mammals) || 1;
        
        const animalProduction = limitNumber(gameState.mammals * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.mammals * baseRate * efficiency * evolutionMultiplier * 1.6);
        
        if (animalProduction > 0 || particleProduction > 0) {
          gameState.animals = limitNumber((Number(gameState.animals) || 0) + animalProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.animals > 0) {
        const efficiency = this.calculateEfficiency(gameState.animals);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.animals) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.animals) || 1;
        
        const fishProduction = limitNumber(gameState.animals * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.animals * baseRate * efficiency * evolutionMultiplier * 1.4);
        
        if (fishProduction > 0 || particleProduction > 0) {
          gameState.fish = limitNumber((Number(gameState.fish) || 0) + fishProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.fish > 0) {
        const efficiency = this.calculateEfficiency(gameState.fish);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.fish) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.fish) || 1;
        
        const wormProduction = limitNumber(gameState.fish * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.fish * baseRate * efficiency * evolutionMultiplier * 1.2);
        
        if (wormProduction > 0 || particleProduction > 0) {
          gameState.worms = limitNumber((Number(gameState.worms) || 0) + wormProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.worms > 0) {
        const efficiency = this.calculateEfficiency(gameState.worms);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.worms) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.worms) || 1;
        
        const organismProduction = limitNumber(gameState.worms * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.worms * baseRate * efficiency * evolutionMultiplier);
        
        if (organismProduction > 0 || particleProduction > 0) {
          gameState.organisms = limitNumber((Number(gameState.organisms) || 0) + organismProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.organisms > 0) {
        const efficiency = this.calculateEfficiency(gameState.organisms);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.organisms) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.organisms) || 1;
        
        const cellProduction = limitNumber(gameState.organisms * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.organisms * baseRate * efficiency * evolutionMultiplier * 0.8);
        
        if (cellProduction > 0 || particleProduction > 0) {
          gameState.cells = limitNumber((Number(gameState.cells) || 0) + cellProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.cells > 0) {
        const efficiency = this.calculateEfficiency(gameState.cells);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.cells) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.cells) || 1;
        
        const membraneProduction = limitNumber(gameState.cells * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.cells * baseRate * efficiency * evolutionMultiplier * 0.6);
        
        if (membraneProduction > 0 || particleProduction > 0) {
          gameState.membrane = limitNumber((Number(gameState.membrane) || 0) + membraneProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.membrane > 0) {
        const efficiency = this.calculateEfficiency(gameState.membrane);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.membrane) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.membrane) || 1;
        
        const proteinProduction = limitNumber(gameState.membrane * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.membrane * baseRate * efficiency * evolutionMultiplier * 0.4);
        
        if (proteinProduction > 0 || particleProduction > 0) {
          gameState.proteins = limitNumber((Number(gameState.proteins) || 0) + proteinProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.proteins > 0) {
        const efficiency = this.calculateEfficiency(gameState.proteins);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.proteins) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.proteins) || 1;
        
        const moleculeProduction = limitNumber(gameState.proteins * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.proteins * baseRate * efficiency * evolutionMultiplier * 0.3);
        
        if (moleculeProduction > 0 || particleProduction > 0) {
          gameState.molecules = limitNumber((Number(gameState.molecules) || 0) + moleculeProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.molecules > 0) {
        const efficiency = this.calculateEfficiency(gameState.molecules);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.molecules) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.molecules) || 1;
        
        const atomProduction = limitNumber(gameState.molecules * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.molecules * baseRate * efficiency * evolutionMultiplier * 0.2);
        
        if (atomProduction > 0 || particleProduction > 0) {
          gameState.atoms = limitNumber((Number(gameState.atoms) || 0) + atomProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.atoms > 0) {
        const efficiency = this.calculateEfficiency(gameState.atoms);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.atoms) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.atoms) || 1;
        
        const nucleiProduction = limitNumber(gameState.atoms * baseRate * efficiency * evolutionMultiplier);
        const particleProduction = limitNumber(gameState.atoms * baseRate * efficiency * evolutionMultiplier * 0.1);
        
        if (nucleiProduction > 0 || particleProduction > 0) {
          gameState.nuclei = limitNumber((Number(gameState.nuclei) || 0) + nucleiProduction);
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (gameState.nuclei > 0) {
        const efficiency = this.calculateEfficiency(gameState.nuclei);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.nuclei) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.nuclei) || 1;
        
        const particleProduction = limitNumber(gameState.nuclei * baseRate * efficiency * evolutionMultiplier);
        
        if (particleProduction > 0) {
          gameState.particles = limitNumber((Number(gameState.particles) || 0) + particleProduction);
          changed = true;
        }
      }

      if (changed) {
        // 确保所有数值都在安全范围内
        Object.keys(gameState).forEach(key => {
          if (typeof gameState[key] === 'number') {
            gameState[key] = limitNumber(gameState[key]);
          }
        });
        
        this.setData({ gameState });
      }
    } catch (error) {
      console.error('Production calculation error:', error);
    }
  },

  // 更新栖息地生产
  updateHabitatProduction() {
    const gameState = this.data.gameState;
    let changed = false;

    if (gameState.stone > 0) {
      const efficiency = this.calculateEfficiency(gameState.stone);
      gameState.territory += Math.floor(gameState.stone * this.data.productionRates.stone * efficiency);
      gameState.particles += Math.floor(gameState.stone * this.data.productionRates.particles * efficiency * 2);
      changed = true;
    }

    if (gameState.mountain > 0) {
      const efficiency = this.calculateEfficiency(gameState.mountain);
      gameState.territory += Math.floor(gameState.mountain * this.data.productionRates.mountain * efficiency);
      gameState.particles += Math.floor(gameState.mountain * this.data.productionRates.particles * efficiency * 3);
      changed = true;
    }

    if (gameState.continent > 0) {
      const efficiency = this.calculateEfficiency(gameState.continent);
      gameState.territory += Math.floor(gameState.continent * this.data.productionRates.continent * efficiency);
      gameState.particles += Math.floor(gameState.continent * this.data.productionRates.particles * efficiency * 4);
      changed = true;
    }

    if (gameState.planet > 0) {
      const efficiency = this.calculateEfficiency(gameState.planet);
      gameState.territory += Math.floor(gameState.planet * this.data.productionRates.planet * efficiency);
      gameState.particles += Math.floor(gameState.planet * this.data.productionRates.particles * efficiency * 5);
      changed = true;
    }

    if (gameState.star > 0) {
      const efficiency = this.calculateEfficiency(gameState.star);
      gameState.territory += Math.floor(gameState.star * this.data.productionRates.star * efficiency);
      gameState.particles += Math.floor(gameState.star * this.data.productionRates.particles * efficiency * 6);
      changed = true;
    }

    if (gameState.galaxy > 0) {
      const efficiency = this.calculateEfficiency(gameState.galaxy);
      gameState.territory += Math.floor(gameState.galaxy * this.data.productionRates.galaxy * efficiency);
      gameState.particles += Math.floor(gameState.galaxy * this.data.productionRates.particles * efficiency * 7);
      changed = true;
    }

    if (gameState.cluster > 0) {
      const efficiency = this.calculateEfficiency(gameState.cluster);
      gameState.territory += Math.floor(gameState.cluster * this.data.productionRates.cluster * efficiency);
      gameState.particles += Math.floor(gameState.cluster * this.data.productionRates.particles * efficiency * 8);
      changed = true;
    }

    if (gameState.blackhole > 0) {
      const efficiency = this.calculateEfficiency(gameState.blackhole);
      gameState.territory += Math.floor(gameState.blackhole * this.data.productionRates.blackhole * efficiency);
      gameState.particles += Math.floor(gameState.blackhole * this.data.productionRates.particles * efficiency * 10);
      changed = true;
    }

    if (changed) {
      this.setData({ gameState });
    }
  },

  // 自动购买
  autoBuy() {
    try {
      const gameState = this.data.gameState;
      let changed = false;

      // 特殊处理原子核的自动购买
      if (gameState.autoNucleus) {
        console.log('尝试自动购买原子核');
        const price = this.data.prices.nuclei;  // 直接使用基础价格
        while (gameState.particles >= price) {  // 循环购买，直到粒子不足
          gameState.particles -= price;
          gameState.nuclei += 1;
          changed = true;
        }
      }

      // 处理其他生物资源的自动购买
      try {
        if (Array.isArray(this.data.biologicalResources)) {
          for (let i = 0; i < this.data.biologicalResources.length; i++) {
            const resource = this.data.biologicalResources[i];
            if (resource && typeof resource === 'object' && typeof resource.key === 'string') {
              const resourceKey = resource.key;
              const autoKey = 'auto' + resourceKey.charAt(0).toUpperCase() + resourceKey.slice(1);
              
              if (gameState[autoKey]) {
                console.log(`尝试自动购买${resource.name}，状态键：${autoKey}，状态值：${gameState[autoKey]}`);
                const price = this.data.prices[resourceKey];
                const currency = this.getResourceCurrency(resourceKey);
                
                if (typeof price === 'number' && typeof currency === 'string') {
                  while (gameState[currency] >= price) {
                    gameState[currency] -= price;
                    gameState[resourceKey] += 1;
                    changed = true;
                  }
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('生物资源自动购买出错:', error);
      }

      // 处理栖息地资源的自动购买
      try {
        if (Array.isArray(this.data.habitatResources)) {
          for (let i = 0; i < this.data.habitatResources.length; i++) {
            const resource = this.data.habitatResources[i];
            if (resource && typeof resource === 'object' && typeof resource.key === 'string') {
              const resourceKey = resource.key;
              const autoKey = 'auto' + resourceKey.charAt(0).toUpperCase() + resourceKey.slice(1);
              
              if (gameState[autoKey]) {
                console.log(`尝试自动购买${resource.name}，状态键：${autoKey}，状态值：${gameState[autoKey]}`);
                const price = this.data.prices[resourceKey];
                
                if (typeof price === 'number') {
                  while (gameState.particles >= price) {
                    gameState.particles -= price;
                    gameState[resourceKey] += 1;
                    changed = true;
                  }
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('栖息地资源自动购买出错:', error);
      }

      if (changed) {
        // 确保所有数值都在安全范围内
        Object.keys(gameState).forEach(key => {
          if (typeof gameState[key] === 'number') {
            gameState[key] = limitNumber(gameState[key]);
          }
        });
        
        this.setData({ gameState });
        this.updateDisplay();
      }
    } catch (error) {
      console.error('Auto buy error:', error);
    }
  },

  // 计算效率（确保返回有效数值）
  calculateEfficiency(count) {
    count = Number(count) || 0;
    if (count <= 0) return 0;
    if (count <= 10) return 1.0;
    if (count <= 100) return 0.95;
    if (count <= 1000) return 0.9;
    if (count <= 10000) return 0.85;
    if (count <= 100000) return 0.8;
    return 0.75;
  },

  // 获取当前价格（直接返回基础价格）
  getCurrentPrice(resource) {
    return this.data.prices[resource] || 0;
  },

  // 获取资源的货币类型
  getResourceCurrency(resource) {
    const resourceConfig = this.data.biologicalResources.find(r => r.key === resource);
    return resourceConfig ? this.getCurrencyKey(resourceConfig.currency) : 'particles';
  },

  // 获取货币键名
  getCurrencyKey(currencyName) {
    const currencyMap = {
      '粒子': 'particles',
      '原子核': 'nuclei',
      '原子': 'atoms',
      '分子': 'molecules',
      '蛋白质': 'proteins',
      '细胞膜': 'membrane',
      '细胞': 'cells',
      '微生物': 'organisms',
      '蠕虫': 'worms',
      '鱼类': 'fish',
      '动物': 'animals',
      '哺乳动物': 'mammals',
      '灵长类': 'apes',
      '智慧生命': 'humans'
    };
    return currencyMap[currencyName] || 'particles';
  },

  // 获取进化成本（调整进化成本）
  getEvolutionCost(resource) {
    const baseCost = 1000;
    const evolutionCount = this.data.gameState.evolutionCounts[resource] || 0;
    return Math.floor(baseCost * Math.pow(5, evolutionCount));
  },

  // 格式化数字（确保返回有效字符串）
  formatNumber(num) {
    if (typeof num !== 'number' || isNaN(num)) return '0';
    if (num < 0) return '0';
    if (num < 1e3) return Math.floor(num).toString();
    
    const exp = Math.floor(Math.log10(num));
    if (exp > 1e308) return 'Infinity';
    
    if (exp >= 4) {
      const mantissa = num / Math.pow(10, exp);
      return `${Math.floor(mantissa)}e${exp}`;
    }
    
    return Math.floor(num).toString();
  },

  // 更新显示
  updateDisplay() {
    const gameState = this.data.gameState;
    const displayData = {};
    const productionRates = {};
    const canEvolve = {};
    const prices = {};

    // 计算并存储当前价格
    this.data.biologicalResources.forEach(resource => {
      prices[resource.key] = this.getCurrentPrice(resource.key);
    });
    prices.nuclei = this.getCurrentPrice('nuclei');

    // 格式化资源数量
    Object.keys(gameState).forEach(key => {
      if (typeof gameState[key] === 'number') {
        displayData[key] = this.formatNumber(Number(gameState[key]) || 0);
      }
    });

    // 计算生产率
    try {
      // 原子核生产粒子
      if (gameState.nuclei > 0) {
        const efficiency = this.calculateEfficiency(gameState.nuclei);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.nuclei) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.nuclei) || 1;
        const production = gameState.nuclei * baseRate * efficiency * evolutionMultiplier;
        productionRates.particles = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.particles = '+0/秒';
      }

      // 原子生产原子核
      if (gameState.atoms > 0) {
        const efficiency = this.calculateEfficiency(gameState.atoms);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.atoms) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.atoms) || 1;
        const production = gameState.atoms * baseRate * efficiency * evolutionMultiplier;
        productionRates.nuclei = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.nuclei = '+0/秒';
      }

      // 分子生产原子
      if (gameState.molecules > 0) {
        const efficiency = this.calculateEfficiency(gameState.molecules);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.molecules) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.molecules) || 1;
        const production = gameState.molecules * baseRate * efficiency * evolutionMultiplier;
        productionRates.atoms = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.atoms = '+0/秒';
      }

      // 蛋白质生产分子
      if (gameState.proteins > 0) {
        const efficiency = this.calculateEfficiency(gameState.proteins);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.proteins) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.proteins) || 1;
        const production = gameState.proteins * baseRate * efficiency * evolutionMultiplier;
        productionRates.molecules = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.molecules = '+0/秒';
      }

      // 细胞膜生产蛋白质
      if (gameState.membrane > 0) {
        const efficiency = this.calculateEfficiency(gameState.membrane);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.membrane) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.membrane) || 1;
        const production = gameState.membrane * baseRate * efficiency * evolutionMultiplier;
        productionRates.proteins = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.proteins = '+0/秒';
      }

      // 细胞生产细胞膜
      if (gameState.cells > 0) {
        const efficiency = this.calculateEfficiency(gameState.cells);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.cells) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.cells) || 1;
        const production = gameState.cells * baseRate * efficiency * evolutionMultiplier;
        productionRates.membrane = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.membrane = '+0/秒';
      }

      // 微生物生产细胞
      if (gameState.organisms > 0) {
        const efficiency = this.calculateEfficiency(gameState.organisms);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.organisms) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.organisms) || 1;
        const production = gameState.organisms * baseRate * efficiency * evolutionMultiplier;
        productionRates.cells = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.cells = '+0/秒';
      }

      // 蠕虫生产微生物
      if (gameState.worms > 0) {
        const efficiency = this.calculateEfficiency(gameState.worms);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.worms) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.worms) || 1;
        const production = gameState.worms * baseRate * efficiency * evolutionMultiplier;
        productionRates.organisms = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.organisms = '+0/秒';
      }

      // 鱼类生产蠕虫
      if (gameState.fish > 0) {
        const efficiency = this.calculateEfficiency(gameState.fish);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.fish) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.fish) || 1;
        const production = gameState.fish * baseRate * efficiency * evolutionMultiplier;
        productionRates.worms = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.worms = '+0/秒';
      }

      // 动物生产鱼类
      if (gameState.animals > 0) {
        const efficiency = this.calculateEfficiency(gameState.animals);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.animals) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.animals) || 1;
        const production = gameState.animals * baseRate * efficiency * evolutionMultiplier;
        productionRates.fish = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.fish = '+0/秒';
      }

      // 哺乳动物生产动物
      if (gameState.mammals > 0) {
        const efficiency = this.calculateEfficiency(gameState.mammals);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.mammals) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.mammals) || 1;
        const production = gameState.mammals * baseRate * efficiency * evolutionMultiplier;
        productionRates.animals = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.animals = '+0/秒';
      }

      // 灵长类生产哺乳动物
      if (gameState.apes > 0) {
        const efficiency = this.calculateEfficiency(gameState.apes);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.apes) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.apes) || 1;
        const production = gameState.apes * baseRate * efficiency * evolutionMultiplier;
        productionRates.mammals = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.mammals = '+0/秒';
      }

      // 智慧生命生产灵长类
      if (gameState.humans > 0) {
        const efficiency = this.calculateEfficiency(gameState.humans);
        const evolutionMultiplier = Math.min(Math.pow(2, Number(gameState.evolutionCounts.humans) || 0), 1e10);
        const baseRate = Number(this.data.productionRates.humans) || 1;
        const production = gameState.humans * baseRate * efficiency * evolutionMultiplier;
        productionRates.apes = `+${this.formatNumber(production)}/秒`;
      } else {
        productionRates.apes = '+0/秒';
      }

      // 检查是否可以进化
      Object.keys(gameState.evolutionCounts).forEach(resource => {
        const evolutionCost = this.getEvolutionCost(resource);
        canEvolve[resource] = gameState.territory >= evolutionCost;
      });

      this.setData({
        displayData,
        productionRates,
        canEvolve,
        prices
      });
    } catch (error) {
      console.error('Display update error:', error);
    }
  }
}); 