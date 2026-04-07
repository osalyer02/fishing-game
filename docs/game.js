const SAVE_VERSION = 1;
const SAVE_KEY = "fishing-rpg-web-save-v1";

const STARTING_DAY = 1;
const STARTING_COINS = 0;
const CASTS_PER_DAY = 5;
const STARTING_MAX_HP = 100;
const STARTING_ROD_ID = "twig_rod";
const STARTING_WEAPON_ID = "driftwood_club";
const FINAL_ROD_ID = "leviathan_rod";
const BOSS_MONSTER_ID = "kraken_sovereign";

const CATEGORY_FISH = "fish";
const CATEGORY_TREASURE = "treasure";
const CATEGORY_JUNK = "junk";
const CATEGORY_MONSTER = "monster";

const RARITY_WEIGHTS = {
  common: 50,
  uncommon: 28,
  rare: 14,
  epic: 6,
  legendary: 2,
  mythic: 0.4,
};

const ROD_TIER_TO_MONSTER_TIER = {
  1: 1,
  2: 1,
  3: 2,
  4: 2,
  5: 3,
  6: 3,
};

const REACTION_WINDOW_MS_BY_ROD_TIER = {
  1: 260,
  2: 320,
  3: 380,
  4: 460,
  5: 560,
  6: 680,
};

const app = {
  content: null,
  state: null,
  scene: "fishing",
  sceneBeforeDiary: "fishing",
  currentEncounter: null,
  minigame: null,
  lastCatch: null,
  log: [],
};

const elements = {
  day: document.getElementById("dayValue"),
  coins: document.getElementById("coinsValue"),
  casts: document.getElementById("castsValue"),
  hp: document.getElementById("hpValue"),
  rod: document.getElementById("rodValue"),
  weapon: document.getElementById("weaponValue"),

  eventBanner: document.getElementById("eventBanner"),

  fishingScene: document.getElementById("fishingScene"),
  shopScene: document.getElementById("shopScene"),
  diaryScene: document.getElementById("diaryScene"),
  combatScene: document.getElementById("combatScene"),
  victoryScene: document.getElementById("victoryScene"),

  fishingHint: document.getElementById("fishingHint"),
  minigameStatus: document.getElementById("minigameStatus"),
  minigameWindow: document.getElementById("minigameWindow"),
  timingBobber: document.getElementById("timingBobber"),
  lastCatch: document.getElementById("lastCatch"),
  castButton: document.getElementById("castButton"),
  reelButton: document.getElementById("reelButton"),

  buyRodButton: document.getElementById("buyRodButton"),
  buyWeaponButton: document.getElementById("buyWeaponButton"),
  activePowerupsText: document.getElementById("activePowerupsText"),

  diarySummary: document.getElementById("diarySummary"),
  diaryFishList: document.getElementById("diaryFishList"),

  fishInventory: document.getElementById("fishInventory"),
  treasureInventory: document.getElementById("treasureInventory"),
  junkInventory: document.getElementById("junkInventory"),

  monsterName: document.getElementById("monsterName"),
  monsterHp: document.getElementById("monsterHp"),
  runButton: document.getElementById("runButton"),

  eventLog: document.getElementById("eventLog"),
};

function mapById(rows) {
  return Object.fromEntries(rows.map((row) => [row.id, row]));
}

async function loadContent() {
  const files = ["rods", "weapons", "fish", "treasure", "junk", "monsters", "powerups"];
  const loaded = await Promise.all(
    files.map(async (name) => {
      const response = await fetch(`content/${name}.json`);
      if (!response.ok) {
        throw new Error(`Failed to load ${name}.json`);
      }
      return [name, await response.json()];
    }),
  );

  const table = Object.fromEntries(loaded);
  const rods = mapById(table.rods);
  const weapons = mapById(table.weapons);

  return {
    rods,
    weapons,
    fish: mapById(table.fish),
    treasure: mapById(table.treasure),
    junk: mapById(table.junk),
    monsters: mapById(table.monsters),
    powerups: mapById(table.powerups),
    rodOrder: [...table.rods].sort((a, b) => a.tier - b.tier).map((row) => row.id),
    weaponOrder: [...table.weapons]
      .sort((a, b) => a.min_damage + a.max_damage - (b.min_damage + b.max_damage) || a.cost - b.cost)
      .map((row) => row.id),
  };
}

function newGameState() {
  return {
    day: STARTING_DAY,
    coins: STARTING_COINS,
    castsRemaining: CASTS_PER_DAY,
    playerHp: STARTING_MAX_HP,
    playerMaxHp: STARTING_MAX_HP,
    equippedRodId: STARTING_ROD_ID,
    equippedWeaponId: STARTING_WEAPON_ID,
    inventory: {
      fish: {},
      treasure: {},
      junk: {},
    },
    fishCaughtCounts: {},
    activePowerups: [],
    bossDefeated: false,
    bossSpawned: false,
  };
}

function sanitizeInventoryBucket(bucket) {
  if (!bucket || typeof bucket !== "object") {
    return {};
  }

  const cleaned = {};
  for (const [itemId, countRaw] of Object.entries(bucket)) {
    const count = Number(countRaw);
    if (Number.isFinite(count) && count > 0) {
      cleaned[itemId] = Math.floor(count);
    }
  }
  return cleaned;
}

function sanitizeState(payload) {
  const fallback = newGameState();
  const safe = payload && typeof payload === "object" ? payload : {};

  const state = {
    day: Number.isFinite(Number(safe.day)) ? Math.max(1, Math.floor(Number(safe.day))) : fallback.day,
    coins: Number.isFinite(Number(safe.coins)) ? Math.max(0, Math.floor(Number(safe.coins))) : fallback.coins,
    castsRemaining: Number.isFinite(Number(safe.castsRemaining))
      ? Math.max(0, Math.floor(Number(safe.castsRemaining)))
      : fallback.castsRemaining,
    playerHp: Number.isFinite(Number(safe.playerHp)) ? Math.floor(Number(safe.playerHp)) : fallback.playerHp,
    playerMaxHp: Number.isFinite(Number(safe.playerMaxHp))
      ? Math.max(1, Math.floor(Number(safe.playerMaxHp)))
      : fallback.playerMaxHp,
    equippedRodId:
      typeof safe.equippedRodId === "string" && safe.equippedRodId in app.content.rods
        ? safe.equippedRodId
        : fallback.equippedRodId,
    equippedWeaponId:
      typeof safe.equippedWeaponId === "string" && safe.equippedWeaponId in app.content.weapons
        ? safe.equippedWeaponId
        : fallback.equippedWeaponId,
    inventory: {
      fish: sanitizeInventoryBucket(safe.inventory?.fish),
      treasure: sanitizeInventoryBucket(safe.inventory?.treasure),
      junk: sanitizeInventoryBucket(safe.inventory?.junk),
    },
    fishCaughtCounts: sanitizeInventoryBucket(safe.fishCaughtCounts),
    activePowerups: Array.isArray(safe.activePowerups)
      ? safe.activePowerups.filter((id) => typeof id === "string" && id in app.content.powerups)
      : [],
    bossDefeated: Boolean(safe.bossDefeated),
    bossSpawned: Boolean(safe.bossSpawned),
  };

  for (const [fishId, count] of Object.entries(state.inventory.fish)) {
    const prior = state.fishCaughtCounts[fishId] || 0;
    state.fishCaughtCounts[fishId] = Math.max(prior, count);
  }

  state.castsRemaining = Math.min(CASTS_PER_DAY, state.castsRemaining);
  state.playerHp = Math.max(1, Math.min(state.playerMaxHp, state.playerHp));

  return state;
}

function loadState() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) {
      return newGameState();
    }

    const parsed = JSON.parse(raw);
    if (parsed?.saveVersion !== SAVE_VERSION) {
      return newGameState();
    }

    return sanitizeState(parsed.state);
  } catch {
    return newGameState();
  }
}

function saveState() {
  const payload = {
    saveVersion: SAVE_VERSION,
    state: app.state,
  };
  localStorage.setItem(SAVE_KEY, JSON.stringify(payload));
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function choice(values) {
  return values[Math.floor(Math.random() * values.length)];
}

function weightedChoice(items) {
  const total = items.reduce((sum, [, weight]) => sum + weight, 0);
  if (total <= 0) {
    throw new Error("Weighted choice requires positive total weight");
  }

  const roll = Math.random() * total;
  let running = 0;
  for (const [item, weight] of items) {
    running += weight;
    if (roll <= running) {
      return item;
    }
  }
  return items[items.length - 1][0];
}

function normalizeCategoryWeights(weights) {
  const safe = {
    fish: Math.max(0, Number(weights.fish) || 0),
    treasure: Math.max(0, Number(weights.treasure) || 0),
    junk: Math.max(0, Number(weights.junk) || 0),
    monster: Math.max(0, Number(weights.monster) || 0),
  };

  const total = safe.fish + safe.treasure + safe.junk + safe.monster;
  if (total <= 0) {
    return { fish: 55, treasure: 5, junk: 35, monster: 5 };
  }

  return {
    fish: (safe.fish / total) * 100,
    treasure: (safe.treasure / total) * 100,
    junk: (safe.junk / total) * 100,
    monster: (safe.monster / total) * 100,
  };
}

function applyPowerupProbabilities(baseWeights) {
  const adjusted = { ...baseWeights };

  for (const powerupId of app.state.activePowerups) {
    const powerup = app.content.powerups[powerupId];
    if (!powerup) {
      continue;
    }
    for (const [key, delta] of Object.entries(powerup.category_delta || {})) {
      adjusted[key] = (adjusted[key] || 0) + delta;
    }
  }

  return normalizeCategoryWeights(adjusted);
}

function rollCategory() {
  const rod = app.content.rods[app.state.equippedRodId];
  const weights = applyPowerupProbabilities(rod.category_weights);
  return weightedChoice([
    [CATEGORY_FISH, weights.fish],
    [CATEGORY_TREASURE, weights.treasure],
    [CATEGORY_JUNK, weights.junk],
    [CATEGORY_MONSTER, weights.monster],
  ]);
}

function adjustedRarityWeights(rod) {
  const weights = { ...RARITY_WEIGHTS };
  const totalTarget = Object.values(weights).reduce((sum, value) => sum + value, 0);
  const multiplier = 1 + rod.fish_rarity_bonus / 100;

  for (const key of Object.keys(weights)) {
    if (key !== "common") {
      weights[key] *= multiplier;
    }
  }

  const nonCommonTotal = Object.entries(weights)
    .filter(([key]) => key !== "common")
    .reduce((sum, [, value]) => sum + value, 0);

  weights.common = Math.max(0.01, totalTarget - nonCommonTotal);
  return weights;
}

function chooseFish(rod) {
  const availableFish = Object.values(app.content.fish).filter((fish) => (fish.min_rod_tier || 1) <= rod.tier);
  if (availableFish.length === 0) {
    throw new Error(`No fish available for rod tier ${rod.tier}`);
  }

  const byRarity = {};
  for (const fish of availableFish) {
    if (!byRarity[fish.rarity]) {
      byRarity[fish.rarity] = [];
    }
    byRarity[fish.rarity].push(fish);
  }

  const rarityWeights = adjustedRarityWeights(rod);
  const availableRarityWeights = Object.entries(rarityWeights).filter(([rarity]) => Array.isArray(byRarity[rarity]));
  const rarity = weightedChoice(availableRarityWeights);
  return choice(byRarity[rarity]);
}

function chooseTreasure(rod) {
  const options = Object.values(app.content.treasure).filter((item) => item.min_rod_tier <= rod.tier);
  const weighted = options.map((item) => {
    const qualityPush = 1 + (rod.tier - item.min_rod_tier) * 0.3;
    const valuePush = 1 + item.sell_value / 400;
    return [item, Math.max(0.1, qualityPush * valuePush)];
  });
  return weightedChoice(weighted);
}

function chooseJunk() {
  return choice(Object.values(app.content.junk));
}

function resolveMonsterEncounter(rod) {
  if (rod.id === FINAL_ROD_ID && !app.state.bossDefeated && !app.state.bossSpawned) {
    app.state.bossSpawned = true;
    return app.content.monsters[BOSS_MONSTER_ID];
  }

  const maxTier = ROD_TIER_TO_MONSTER_TIER[rod.tier] || 1;
  const candidates = Object.values(app.content.monsters).filter((monster) => !monster.boss && monster.tier <= maxTier);
  const weighted = candidates.map((monster) => [monster, 1 + monster.tier * 0.25 + monster.reward / 100]);
  return weightedChoice(weighted);
}

function addToInventory(category, itemId) {
  const bucket = app.state.inventory[category];
  bucket[itemId] = (bucket[itemId] || 0) + 1;
}

function recordFishCatch(fishId) {
  app.state.fishCaughtCounts[fishId] = (app.state.fishCaughtCounts[fishId] || 0) + 1;
}

function resolveCatchOutcome() {
  const rod = app.content.rods[app.state.equippedRodId];
  const category = rollCategory();

  if (category === CATEGORY_FISH) {
    const fish = chooseFish(rod);
    addToInventory(CATEGORY_FISH, fish.id);
    recordFishCatch(fish.id);
    return {
      category,
      itemId: fish.id,
      itemName: fish.name,
      sellValue: fish.sell_value,
      message: `Caught fish: ${fish.name} (value ${fish.sell_value})`,
    };
  }

  if (category === CATEGORY_TREASURE) {
    const treasure = chooseTreasure(rod);
    addToInventory(CATEGORY_TREASURE, treasure.id);
    return {
      category,
      itemId: treasure.id,
      itemName: treasure.name,
      sellValue: treasure.sell_value,
      message: `Recovered treasure: ${treasure.name} (value ${treasure.sell_value})`,
    };
  }

  if (category === CATEGORY_JUNK) {
    const junk = chooseJunk();
    addToInventory(CATEGORY_JUNK, junk.id);
    return {
      category,
      itemId: junk.id,
      itemName: junk.name,
      sellValue: junk.sell_value,
      message: `Pulled up junk: ${junk.name} (value ${junk.sell_value})`,
    };
  }

  const monster = resolveMonsterEncounter(rod);
  return {
    category: CATEGORY_MONSTER,
    itemId: monster.id,
    itemName: monster.name,
    monster,
    sellValue: monster.reward,
    message: `A monster strikes: ${monster.name}!`,
  };
}

function reactionWindowMsForRodTier(rodTier) {
  return REACTION_WINDOW_MS_BY_ROD_TIER[rodTier] || 300;
}

function startCastMinigame() {
  if (app.state.castsRemaining <= 0) {
    return { success: false, message: "No casts left today. Visit the shop and end your day." };
  }

  app.state.castsRemaining -= 1;
  const rod = app.content.rods[app.state.equippedRodId];
  const now = Date.now();
  app.minigame = {
    castStartedAt: now,
    biteAt: now + randomInt(900, 2900),
    sunkAt: null,
    reactionWindowMs: reactionWindowMsForRodTier(rod.tier),
  };
  return { success: true };
}

function missCurrentCast(message) {
  app.lastCatch = {
    category: "none",
    itemId: null,
    itemName: "Nothing",
    sellValue: 0,
    message,
  };
  app.minigame = null;
  notify(message, "warning");
  if (app.state.castsRemaining <= 0) {
    notify("No casts left. Visit the shop and end day.", "warning");
  }
}

function onMinigameReelAttempt() {
  if (!app.minigame) {
    notify("Cast first, then reel on bite.", "warning");
    render();
    return;
  }

  const now = Date.now();
  if (app.minigame.sunkAt === null) {
    missCurrentCast("Too early! You yanked the line before the bite.");
    saveState();
    render();
    return;
  }

  if (now <= app.minigame.sunkAt + app.minigame.reactionWindowMs) {
    const result = resolveCatchOutcome();
    app.lastCatch = result;
    app.minigame = null;

    if (result.category === CATEGORY_FISH) {
      notify(result.message, "success");
    } else if (result.category === CATEGORY_MONSTER) {
      notify(result.message, "error");
    } else {
      notify(result.message, "warning");
    }

    if (result.category === CATEGORY_MONSTER && result.monster) {
      app.currentEncounter = startEncounter(result.monster);
      setScene("combat");
      notify("Combat begins: Attack or Run.", "error");
    } else if (app.state.castsRemaining <= 0 && app.scene === "fishing") {
      notify("No casts left. Visit the shop and end day.", "warning");
    }

    saveState();
    render();
    return;
  }

  missCurrentCast("Too slow! The fish stole your bait.");
  saveState();
  render();
}

function tickMinigame() {
  if (app.scene !== "fishing" || !app.minigame) {
    return;
  }

  const now = Date.now();
  if (app.minigame.sunkAt === null && now >= app.minigame.biteAt) {
    app.minigame.sunkAt = now;
    notify("Bite! Click Reel In now!", "warning");
    render();
    return;
  }

  if (app.minigame.sunkAt !== null && now > app.minigame.sunkAt + app.minigame.reactionWindowMs) {
    missCurrentCast("Too slow! The fish stole your bait.");
    saveState();
    render();
    return;
  }

  // Keep timing UI responsive while a cast is active.
  render();
}

function startEncounter(monster) {
  return {
    monster,
    enemyHp: monster.hp,
    finished: false,
    playerWon: false,
  };
}

function weaponBonusFromPowerups() {
  return app.state.activePowerups.reduce((sum, powerupId) => {
    const powerup = app.content.powerups[powerupId];
    return sum + (powerup ? powerup.weapon_damage_bonus : 0);
  }, 0);
}

function rollPlayerDamage(weapon) {
  const base = randomInt(weapon.min_damage, weapon.max_damage);
  const jitter = randomInt(-2, 2);
  const total = base + jitter + weaponBonusFromPowerups();
  return Math.max(1, total);
}

function rollEnemyDamage(monster) {
  return Math.max(1, monster.attack + randomInt(-2, 2));
}

function playerAttack() {
  const encounter = app.currentEncounter;
  if (!encounter || encounter.finished) {
    return { log: ["Combat already resolved."], combatOver: true, playerWon: Boolean(encounter?.playerWon) };
  }

  const weapon = app.content.weapons[app.state.equippedWeaponId];
  const playerDamage = rollPlayerDamage(weapon);
  encounter.enemyHp -= playerDamage;

  const log = [`You hit ${encounter.monster.name} for ${playerDamage}.`];

  if (encounter.enemyHp <= 0) {
    encounter.finished = true;
    encounter.playerWon = true;
    app.state.coins += encounter.monster.reward;
    if (encounter.monster.boss) {
      app.state.bossDefeated = true;
    }
    log.push(`${encounter.monster.name} is defeated! Reward +${encounter.monster.reward} coins.`);
    return { log, combatOver: true, playerWon: true };
  }

  const enemyDamage = rollEnemyDamage(encounter.monster);
  app.state.playerHp = Math.max(0, app.state.playerHp - enemyDamage);
  log.push(`${encounter.monster.name} strikes back for ${enemyDamage}.`);

  if (app.state.playerHp <= 0) {
    encounter.finished = true;
    encounter.playerWon = false;
    const coinLoss = app.state.coins > 0 ? Math.max(5, Math.floor(app.state.coins * 0.2)) : 0;
    app.state.coins = Math.max(0, app.state.coins - coinLoss);
    app.state.playerHp = 1;
    log.push(`You were overwhelmed and washed ashore. Lost ${coinLoss} coins.`);
    return { log, combatOver: true, playerWon: false };
  }

  return { log, combatOver: false, playerWon: false };
}

function attemptRun() {
  const encounter = app.currentEncounter;
  if (!encounter || encounter.finished) {
    return { log: ["Combat already resolved."], combatOver: true, playerWon: Boolean(encounter?.playerWon) };
  }

  if (Math.random() < 0.35) {
    encounter.finished = true;
    encounter.playerWon = false;
    return { log: ["You escaped the fight!"], combatOver: true, playerWon: false };
  }

  const enemyDamage = rollEnemyDamage(encounter.monster);
  app.state.playerHp = Math.max(0, app.state.playerHp - enemyDamage);
  const log = [`Escape failed! ${encounter.monster.name} hits for ${enemyDamage}.`];

  if (app.state.playerHp <= 0) {
    encounter.finished = true;
    encounter.playerWon = false;
    app.state.playerHp = 1;
    log.push("You barely survive and crawl back to shore.");
    return { log, combatOver: true, playerWon: false };
  }

  return { log, combatOver: false, playerWon: false };
}

function clearCategory(category) {
  const sold = { ...app.state.inventory[category] };
  app.state.inventory[category] = {};
  return sold;
}

function itemSellValue(category, itemId) {
  if (category === CATEGORY_FISH) {
    return app.content.fish[itemId]?.sell_value || 0;
  }
  if (category === CATEGORY_TREASURE) {
    return app.content.treasure[itemId]?.sell_value || 0;
  }
  if (category === CATEGORY_JUNK) {
    return app.content.junk[itemId]?.sell_value || 0;
  }
  return 0;
}

function sellAllCategory(category) {
  const sold = clearCategory(category);
  const soldEntries = Object.entries(sold);
  if (soldEntries.length === 0) {
    return { success: false, message: `No ${category} to sell.` };
  }

  const total = soldEntries.reduce((sum, [itemId, count]) => sum + itemSellValue(category, itemId) * count, 0);
  app.state.coins += total;
  return { success: true, message: `Sold all ${category} for ${total} coins.` };
}

function nextId(order, currentId) {
  const idx = order.indexOf(currentId);
  if (idx === -1 || idx + 1 >= order.length) {
    return null;
  }
  return order[idx + 1];
}

function buyNextRod() {
  const nextRodId = nextId(app.content.rodOrder, app.state.equippedRodId);
  if (!nextRodId) {
    return { success: false, message: "You already own the best rod." };
  }

  const rod = app.content.rods[nextRodId];
  if (app.state.coins < rod.cost) {
    return { success: false, message: "Not enough coins for that rod." };
  }

  app.state.coins -= rod.cost;
  app.state.equippedRodId = rod.id;
  return { success: true, message: `Purchased and equipped ${rod.name}.` };
}

function buyNextWeapon() {
  const nextWeaponId = nextId(app.content.weaponOrder, app.state.equippedWeaponId);
  if (!nextWeaponId) {
    return { success: false, message: "You already own the best weapon." };
  }

  const weapon = app.content.weapons[nextWeaponId];
  if (app.state.coins < weapon.cost) {
    return { success: false, message: "Not enough coins for that weapon." };
  }

  app.state.coins -= weapon.cost;
  app.state.equippedWeaponId = weapon.id;
  return { success: true, message: `Purchased and equipped ${weapon.name}.` };
}

function buyPowerup(powerupId) {
  const powerup = app.content.powerups[powerupId];
  if (!powerup) {
    return { success: false, message: "Unknown power-up." };
  }

  if (app.state.activePowerups.includes(powerup.id)) {
    return { success: false, message: "That power-up is already active today." };
  }

  if (app.state.coins < powerup.cost) {
    return { success: false, message: "Not enough coins for that power-up." };
  }

  app.state.coins -= powerup.cost;
  app.state.activePowerups.push(powerup.id);
  return { success: true, message: `Activated ${powerup.name} for the day.` };
}

function canEndDay() {
  return app.state.castsRemaining <= 0;
}

function advanceDay() {
  app.state.day += 1;
  app.state.castsRemaining = CASTS_PER_DAY;
  app.state.playerHp = app.state.playerMaxHp;
  app.state.activePowerups = [];
}

function combatLevel(message, combatOver, playerWon) {
  const lowered = message.toLowerCase();
  if (lowered.includes("escaped")) {
    return "info";
  }
  if (playerWon) {
    return "success";
  }
  if (combatOver) {
    return "error";
  }
  return "warning";
}

function setScene(scene) {
  app.scene = scene;
}

function notify(message, level = "info") {
  elements.eventBanner.textContent = message;
  elements.eventBanner.className = `panel event-banner ${level}`;
  app.log.unshift({ message, level, day: app.state.day, at: new Date().toLocaleTimeString() });
  app.log = app.log.slice(0, 80);
}

function onCastLine() {
  if (app.scene !== "fishing") {
    return;
  }

  if (app.minigame) {
    onMinigameReelAttempt();
    return;
  }

  const startResult = startCastMinigame();
  if (!startResult.success) {
    notify(startResult.message, "error");
    saveState();
    render();
    return;
  }

  app.lastCatch = null;
  notify("Line cast. Watch the bobber, then reel quickly when it sinks.", "info");

  saveState();
  render();
}

function onOpenShop() {
  if (app.scene === "combat" || app.scene === "victory" || app.scene === "diary") {
    return;
  }
  if (app.minigame) {
    notify("Finish your current cast before leaving the lake.", "warning");
    return;
  }
  setScene("shop");
  notify("Entered shop. Sell, upgrade, and end day when ready.", "info");
  saveState();
  render();
}

function onOpenDiary() {
  if (app.scene !== "fishing" && app.scene !== "shop") {
    return;
  }
  if (app.scene === "fishing" && app.minigame) {
    notify("Finish your current cast before opening the diary.", "warning");
    return;
  }
  app.sceneBeforeDiary = app.scene;
  setScene("diary");
  notify("Opened diary.", "info");
  render();
}

function onCloseDiary() {
  if (app.scene !== "diary") {
    return;
  }
  setScene(app.sceneBeforeDiary || "fishing");
  notify("Closed diary.", "info");
  render();
}

function onBackToLake() {
  if (app.scene !== "shop") {
    return;
  }
  setScene("fishing");
  notify("Back at the lake.", "info");
  saveState();
  render();
}

function onShopAction(result) {
  notify(result.message, result.success ? "info" : "error");
  saveState();
  render();
}

function onEndDay() {
  if (!canEndDay()) {
    notify("Spend all 5 casts before ending the day.", "error");
    render();
    return;
  }

  advanceDay();
  setScene("fishing");
  notify(`A new dawn: Day ${app.state.day}.`, "success");
  saveState();
  render();
}

function resolveCombatIfOver(turnResult) {
  if (!turnResult.combatOver || !app.currentEncounter) {
    return;
  }

  const monster = app.currentEncounter.monster;
  if (turnResult.playerWon && monster.boss && app.state.bossDefeated) {
    setScene("victory");
    notify("The Kraken Sovereign falls. You are legend!", "success");
  } else {
    setScene("fishing");
    notify("Combat resolved. Return to fishing.", turnResult.playerWon ? "info" : "warning");
  }

  app.currentEncounter = null;
}

function onAttack() {
  if (app.scene !== "combat") {
    return;
  }

  const turnResult = playerAttack();
  const joined = turnResult.log.join(" ");
  notify(joined, combatLevel(joined, turnResult.combatOver, turnResult.playerWon));
  resolveCombatIfOver(turnResult);
  saveState();
  render();
}

function onRun() {
  if (app.scene !== "combat" || !app.currentEncounter) {
    return;
  }

  if (app.currentEncounter.monster.boss) {
    notify("You cannot flee the Kraken Sovereign.", "error");
    render();
    return;
  }

  const turnResult = attemptRun();
  const joined = turnResult.log.join(" ");
  notify(joined, combatLevel(joined, turnResult.combatOver, turnResult.playerWon));
  resolveCombatIfOver(turnResult);
  saveState();
  render();
}

function startNewRun() {
  app.state = newGameState();
  app.scene = "fishing";
  app.sceneBeforeDiary = "fishing";
  app.currentEncounter = null;
  app.minigame = null;
  app.lastCatch = null;
  app.log = [];
  notify("Fresh start: Day 1.", "success");
  saveState();
  render();
}

function categoryDisplayName(category) {
  if (category === CATEGORY_FISH) {
    return "fish";
  }
  if (category === CATEGORY_TREASURE) {
    return "treasure";
  }
  if (category === CATEGORY_JUNK) {
    return "junk";
  }
  return category;
}

function renderSceneVisibility() {
  const scenes = {
    fishing: elements.fishingScene,
    shop: elements.shopScene,
    diary: elements.diaryScene,
    combat: elements.combatScene,
    victory: elements.victoryScene,
  };

  for (const [key, node] of Object.entries(scenes)) {
    node.classList.toggle("hidden", app.scene !== key);
  }
}

function renderStatus() {
  const rod = app.content.rods[app.state.equippedRodId];
  const weapon = app.content.weapons[app.state.equippedWeaponId];

  elements.day.textContent = String(app.state.day);
  elements.coins.textContent = String(app.state.coins);
  elements.casts.textContent = String(app.state.castsRemaining);
  elements.hp.textContent = `${app.state.playerHp} / ${app.state.playerMaxHp}`;
  elements.rod.textContent = rod.name;
  elements.weapon.textContent = weapon.name;

  if (app.minigame) {
    if (app.minigame.sunkAt === null) {
      elements.fishingHint.textContent = "Wait for the bobber to sink, then reel in fast.";
    } else {
      elements.fishingHint.textContent = "Bite! Reel in now before the fish gets away.";
    }
  } else if (app.state.castsRemaining <= 0) {
    elements.fishingHint.textContent = "No casts left. Visit the shop, sell loot, and end day.";
  } else {
    elements.fishingHint.textContent = "Cast and react fast when the bobber sinks.";
  }
}

function renderLastCatch() {
  if (!app.lastCatch) {
    elements.lastCatch.textContent = "No casts yet today.";
    return;
  }
  elements.lastCatch.textContent = app.lastCatch.message;
}

function renderMinigame() {
  const castButton = elements.castButton;
  const reelButton = elements.reelButton;
  if (!castButton || !reelButton) {
    return;
  }

  if (!app.minigame) {
    elements.minigameStatus.textContent = "No cast active.";
    elements.minigameWindow.textContent = "Reaction window: -";
    elements.timingBobber.style.left = "4px";
    castButton.textContent = "Cast Line";
    castButton.disabled = app.state.castsRemaining <= 0;
    reelButton.disabled = true;
    return;
  }

  const now = Date.now();
  const trackWidth = Math.max(12, (elements.timingBobber.parentElement?.clientWidth || 248) - 12);

  if (app.minigame.sunkAt === null) {
    const total = Math.max(1, app.minigame.biteAt - app.minigame.castStartedAt);
    const elapsed = Math.max(0, now - app.minigame.castStartedAt);
    const progress = Math.min(1, elapsed / total);
    elements.timingBobber.style.left = `${4 + progress * trackWidth}px`;
    elements.minigameStatus.textContent = "Waiting... watch the bobber.";
    elements.minigameWindow.textContent = `Reaction window: ${(app.minigame.reactionWindowMs / 1000).toFixed(2)}s`;
    castButton.textContent = "Casting...";
    castButton.disabled = true;
    reelButton.disabled = false;
    return;
  }

  const remainingMs = Math.max(0, app.minigame.sunkAt + app.minigame.reactionWindowMs - now);
  const progress = 1 - remainingMs / Math.max(1, app.minigame.reactionWindowMs);
  elements.timingBobber.style.left = `${4 + Math.min(1, progress) * trackWidth}px`;
  elements.minigameStatus.textContent = "Bite! Reel now!";
  elements.minigameWindow.textContent = `Time left: ${(remainingMs / 1000).toFixed(2)}s`;
  castButton.textContent = "Casting...";
  castButton.disabled = true;
  reelButton.disabled = false;
}

function renderInventoryList(node, category) {
  const bucket = app.state.inventory[category];
  const entries = Object.entries(bucket);

  if (entries.length === 0) {
    node.innerHTML = `<li>No ${categoryDisplayName(category)}.</li>`;
    return;
  }

  const rows = entries
    .map(([itemId, count]) => {
      const item = app.content[category][itemId];
      if (!item) {
        return null;
      }
      const total = item.sell_value * count;
      return { label: item.name, count, total };
    })
    .filter(Boolean)
    .sort((a, b) => a.label.localeCompare(b.label));

  node.innerHTML = rows
    .map((row) => `<li>${row.label} x${row.count} <span class="small-note">(${row.total}c)</span></li>`)
    .join("");
}

function renderInventory() {
  renderInventoryList(elements.fishInventory, CATEGORY_FISH);
  renderInventoryList(elements.treasureInventory, CATEGORY_TREASURE);
  renderInventoryList(elements.junkInventory, CATEGORY_JUNK);
}

function renderDiary() {
  const entries = Object.entries(app.state.fishCaughtCounts)
    .map(([fishId, count]) => {
      const fish = app.content.fish[fishId];
      if (!fish || count <= 0) {
        return null;
      }
      return {
        id: fishId,
        name: fish.name,
        rarity: fish.rarity,
        minRodTier: fish.min_rod_tier || 1,
        count,
        sellValue: fish.sell_value,
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.minRodTier - b.minRodTier || a.name.localeCompare(b.name));

  elements.diarySummary.textContent = `Discovered ${entries.length} / ${Object.keys(app.content.fish).length} species.`;

  if (entries.length === 0) {
    elements.diaryFishList.innerHTML = "<li>No fish discovered yet.</li>";
    return;
  }

  elements.diaryFishList.innerHTML = entries
    .map(
      (entry) =>
        `<li>T${entry.minRodTier} ${entry.name} <span class="small-note">[${entry.rarity}] x${entry.count} (${entry.sellValue}c)</span></li>`,
    )
    .join("");
}

function renderShop() {
  const nextRodId = nextId(app.content.rodOrder, app.state.equippedRodId);
  if (!nextRodId) {
    elements.buyRodButton.textContent = "Best Rod Owned";
    elements.buyRodButton.disabled = true;
  } else {
    const rod = app.content.rods[nextRodId];
    elements.buyRodButton.textContent = `Buy ${rod.name} (${rod.cost}c)`;
    elements.buyRodButton.disabled = app.state.coins < rod.cost;
  }

  const nextWeaponId = nextId(app.content.weaponOrder, app.state.equippedWeaponId);
  if (!nextWeaponId) {
    elements.buyWeaponButton.textContent = "Best Weapon Owned";
    elements.buyWeaponButton.disabled = true;
  } else {
    const weapon = app.content.weapons[nextWeaponId];
    elements.buyWeaponButton.textContent = `Buy ${weapon.name} (${weapon.cost}c)`;
    elements.buyWeaponButton.disabled = app.state.coins < weapon.cost;
  }

  const powerupButtons = document.querySelectorAll(".powerup-btn");
  for (const button of powerupButtons) {
    const powerupId = button.dataset.powerupId;
    const powerup = app.content.powerups[powerupId];
    if (!powerup) {
      continue;
    }

    const active = app.state.activePowerups.includes(powerup.id);
    button.textContent = `${powerup.name} (${powerup.cost}c) - ${powerup.description}`;
    button.disabled = active || app.state.coins < powerup.cost;
  }

  if (app.state.activePowerups.length === 0) {
    elements.activePowerupsText.textContent = "No active power-ups.";
  } else {
    const names = app.state.activePowerups.map((id) => app.content.powerups[id]?.name).filter(Boolean);
    elements.activePowerupsText.textContent = `Active today: ${names.join(", ")}`;
  }
}

function renderCombat() {
  if (!app.currentEncounter) {
    elements.monsterName.textContent = "-";
    elements.monsterHp.textContent = "HP: -";
    elements.runButton.disabled = false;
    return;
  }

  elements.monsterName.textContent = app.currentEncounter.monster.name;
  elements.monsterHp.textContent = `HP: ${Math.max(0, app.currentEncounter.enemyHp)} / ${app.currentEncounter.monster.hp}`;
  elements.runButton.disabled = Boolean(app.currentEncounter.monster.boss);
}

function renderLog() {
  if (app.log.length === 0) {
    elements.eventLog.innerHTML = "<li>No events yet.</li>";
    return;
  }

  elements.eventLog.innerHTML = app.log
    .map(
      (entry) =>
        `<li class="${entry.level}"><strong>Day ${entry.day}</strong> [${entry.at}] ${entry.message}</li>`,
    )
    .join("");
}

function render() {
  renderSceneVisibility();
  renderStatus();
  renderMinigame();
  renderLastCatch();
  renderInventory();
  renderDiary();
  renderShop();
  renderCombat();
  renderLog();
}

function bindEvents() {
  elements.castButton?.addEventListener("click", onCastLine);
  elements.reelButton?.addEventListener("click", onMinigameReelAttempt);
  document.getElementById("openShopButton").addEventListener("click", onOpenShop);
  document.getElementById("openDiaryButton").addEventListener("click", onOpenDiary);
  document.getElementById("backToLakeButton").addEventListener("click", onBackToLake);
  document.getElementById("openDiaryFromShopButton").addEventListener("click", onOpenDiary);
  document.getElementById("closeDiaryButton").addEventListener("click", onCloseDiary);

  document.getElementById("sellFishButton").addEventListener("click", () => onShopAction(sellAllCategory(CATEGORY_FISH)));
  document
    .getElementById("sellTreasureButton")
    .addEventListener("click", () => onShopAction(sellAllCategory(CATEGORY_TREASURE)));
  document.getElementById("sellJunkButton").addEventListener("click", () => onShopAction(sellAllCategory(CATEGORY_JUNK)));

  document.getElementById("buyRodButton").addEventListener("click", () => onShopAction(buyNextRod()));
  document.getElementById("buyWeaponButton").addEventListener("click", () => onShopAction(buyNextWeapon()));

  document.querySelectorAll(".powerup-btn").forEach((button) => {
    button.addEventListener("click", () => {
      onShopAction(buyPowerup(button.dataset.powerupId));
    });
  });

  document.getElementById("endDayButton").addEventListener("click", onEndDay);

  document.getElementById("attackButton").addEventListener("click", onAttack);
  document.getElementById("runButton").addEventListener("click", onRun);

  document.getElementById("newGameButton").addEventListener("click", startNewRun);
  document.getElementById("victoryNewRunButton").addEventListener("click", startNewRun);

  document.addEventListener("keydown", (event) => {
    if (event.key === " " || event.code === "Space") {
      if (app.scene === "fishing") {
        event.preventDefault();
        onMinigameReelAttempt();
      }
      return;
    }

    if (event.key.toLowerCase() === "f") {
      if (app.scene === "fishing" && !app.minigame) {
        onCastLine();
      }
      return;
    }

    if (event.key.toLowerCase() === "d") {
      if (app.scene === "fishing" || app.scene === "shop") {
        onOpenDiary();
      } else if (app.scene === "diary") {
        onCloseDiary();
      }
      return;
    }

    if (event.key.toLowerCase() === "escape" && app.scene === "diary") {
      onCloseDiary();
    }
  });
}

async function init() {
  try {
    app.content = await loadContent();
    app.state = loadState();
    app.scene = app.state.bossDefeated ? "victory" : "fishing";
    app.sceneBeforeDiary = "fishing";
    app.minigame = null;
    bindEvents();
    notify("Welcome to Fishing RPG Web. Cast 5 times, then shop and end your day.", "info");
    render();
    setInterval(tickMinigame, 60);
    saveState();
  } catch (error) {
    elements.eventBanner.className = "panel event-banner error";
    elements.eventBanner.textContent = `Failed to start game: ${error.message}`;
  }
}

init();
