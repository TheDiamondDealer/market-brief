window.scenarioAssets = {
  gold: {
    name: 'Gold', symbol: 'OANDA:XAUUSD', current: 4072, unit: 'USD/oz', presets: [3980, 4050, 4100, 4150, 4200],
    upside: [['Rates','US real and nominal yields need to fall, reducing the opportunity cost of holding gold.'],['US dollar','DXY weakness would remove the strongest current headwind.'],['Macro catalyst','Softer CPI, weaker employment or a dovish Fed repricing would improve the path.'],['Haven override','Gold would need to rise despite firm oil or geopolitical stress, showing haven demand has regained control.'],['Flows','ETF inflows, central-bank demand or futures buying would need to confirm the move.']],
    downside: [['Rates','US 10-year and real yields remain high or break upward.'],['US dollar','DXY strengthens as policy expectations turn more hawkish.'],['Macro catalyst','Hot CPI or strong labour data preserves tightening risk.'],['Technical confirmation','A daily close below $4,050 would strengthen the active bearish trigger.'],['Positioning','Crowded haven positions liquidate after another failed safe-haven reaction.']],
    confirmUp: 'Close above $4,150, ideally while DXY and yields fall.', confirmDown: 'Close below $4,050 with DXY ≥101 and US 10Y ≥4.60%.',
    invalidUp: 'Gold fails above $4,100 and yields/DXY continue rising.', invalidDown: 'Gold closes above $4,150 or rises for two sessions alongside oil, DXY and yields.'
  },
  copper: {
    name: 'Copper', symbol: 'COMEX:HG1!', current: 6.22, unit: 'USD/lb', presets: [6.00, 6.10, 6.25, 6.30, 6.50],
    upside: [['China demand','Credit, grids, manufacturing and property activity need to improve together.'],['Physical market','Visible inventories fall and regional premiums strengthen.'],['Supply','Mine disruptions or lower treatment charges signal concentrate tightness.'],['US dollar','DXY weakness would reduce the financial headwind.'],['Cross-market confirmation','LME, COMEX and Shanghai copper should rise together rather than diverge.']],
    downside: [['China demand','Property, credit or manufacturing data weaken further.'],['Inventories','Exchange stocks rebuild and physical premiums soften.'],['US dollar','A stronger dollar tightens global financial conditions.'],['Supply response','Mine and scrap supply improve faster than demand.'],['Positioning','Speculative longs unwind without physical buyers replacing them.']],
    confirmUp: 'Close above $6.30/lb with falling inventories and aligned LME/ShFE strength.', confirmDown: 'Close below $6.10/lb with weaker China and physical-market evidence.',
    invalidUp: 'Price returns inside $6.10–6.25 while inventories rise.', invalidDown: 'Physical premiums and inventory draws strengthen despite a temporary price dip.'
  },
  silver: {
    name: 'Silver', symbol: 'OANDA:XAGUSD', current: 59.56, unit: 'USD/oz', presets: [55, 58, 60, 62, 65],
    upside: [['Gold channel','Gold must stabilise or rise as yields and the dollar soften.'],['Industrial demand','Copper, solar and manufacturing signals need to improve.'],['Flows','ETF or futures demand must absorb silver’s higher volatility.'],['Macro catalyst','Softer inflation or labour data would support precious metals through rates.'],['Relative value','The gold/silver ratio would need to compress as silver outperforms.']],
    downside: [['Rates and USD','Higher yields and a stronger dollar pressure the precious complex.'],['Industrial cycle','China or global manufacturing expectations weaken.'],['Volatility','Risk reduction forces liquidation in higher-beta silver positions.'],['Gold failure','Gold remains unable to attract haven demand.'],['Positioning','Crowded speculative exposure unwinds.']],
    confirmUp: 'Silver outperforms gold while copper and industrial data improve.', confirmDown: 'Silver breaks support with gold weak, DXY/yields firm and industrial metals soft.',
    invalidUp: 'Silver rallies alone without gold, copper or flow confirmation.', invalidDown: 'Gold stabilises, yields fall and industrial demand indicators turn higher.'
  }
};
