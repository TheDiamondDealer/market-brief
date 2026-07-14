(() => {
  'use strict';

  // Retained as a compatibility shim because index.html historically loaded this
  // path. BR-14 moved the home route to features/command-centre/command-page.js.
  // Do not restore the retired composite risk gauge or hidden bias totals here.
  window.MarketBriefLegacy = window.MarketBriefLegacy || {};
  window.MarketBriefLegacy.commandCentreRetired = true;
})();
