# CarbonTally Insight — Customer, Consultant & External Auditor Question Library

**Date:** 2026-09-22  
**Purpose:** Product/reference library for questions CarbonTally Insight may eventually answer with authoritative CarbonTally data and verifiable evidence.  
**Status:** Design/reference only — not implementation authorization.

---

## 1. Design principle

CarbonTally Insight should support questions that a customer, carbon consultant, reviewer, or external auditor could reasonably ask about a carbon inventory.

The key product rule is:

> **A natural-language answer is useful only when the underlying claim can be traced to an authoritative CarbonTally record, calculation, factor, methodology, or source document.**

For customer-specific numerical claims, Insight should prefer:

`Question → structured intent → authorized deterministic retrieval → authoritative record → evidence/provenance → plain-English explanation`

The LLM should explain verified facts; it should not invent, independently recalculate, or silently choose accounting treatments.

---

# 2. Question classes

The library is organized into:

1. Executive / overall footprint
2. Scope 1
3. Scope 2
4. Scope 3
5. Scope 3 categories 1–15
6. Supplier / value-chain questions
7. Emission-factor questions
8. Calculation-method questions
9. Activity/input questions
10. Trend / variance / hotspot questions
11. Data-quality questions
12. Evidence / provenance questions
13. Audit / assurance questions
14. Reporting / disclosure questions
15. Methodology / boundary questions
16. Consultant investigation questions
17. External-auditor challenge questions
18. Evidence and limitation questions
19. Future analytical questions

The presence of a question in this document does **not** mean CarbonTally currently supports it.

---

# 3. Executive / overall footprint

### Customers

1. What are my total emissions for 2025?
2. How much of my total footprint is Scope 1, Scope 2 and Scope 3?
3. Which scope contributes the most to my footprint?
4. How did my total emissions change compared with last year?
5. What caused the change in my total emissions?
6. Which activities contribute most to my footprint?
7. Which suppliers contribute most to my footprint?
8. Which facilities contribute most to my emissions?
9. Which reporting period has the highest emissions?
10. What are my largest emission hotspots?
11. What percentage of my emissions is supported by primary data?
12. What percentage is estimated or based on secondary data?
13. Which emissions have the weakest data quality?
14. Which results have the strongest evidence?
15. Which parts of my inventory should I investigate first?

### Consultant / reviewer

16. What is the organization's total reported footprint and how is it distributed?
17. Which sources drive the inventory?
18. Which categories dominate the inventory?
19. Where are the largest data-quality gaps?
20. Which results depend most heavily on assumptions or secondary factors?

---

# 4. Scope 1 questions

### Direct-emission identification

21. What are my Scope 1 emissions?
22. Which activities are included in Scope 1?
23. Which facilities generate the most Scope 1 emissions?
24. Which fuels contribute most to Scope 1?
25. Which combustion sources contribute most?
26. What are my stationary combustion emissions?
27. What are my mobile combustion emissions?
28. What are my fugitive emissions?
29. What are my process emissions?
30. Which Scope 1 source increased the most this year?

### Calculation explanation

31. How was this Scope 1 emission calculated?
32. What activity data was used?
33. Which fuel quantity was used?
34. Which unit conversion was applied?
35. Which emission factor was used?
36. Which factor source and year were used?
37. Which gases were included in the calculation?
38. Which GWP basis was used, if recorded?
39. Can you show the calculation inputs and result?
40. Can you show the source document for this Scope 1 result?

---

# 5. Scope 2 questions

### Overall

41. What are my Scope 2 emissions?
42. Which facilities have the highest Scope 2 emissions?
43. How much electricity consumption drives my Scope 2 footprint?
44. Which site consumes the most electricity?
45. Which site has the highest emissions per unit of electricity?
46. How did electricity-related emissions change from last year?

### Location-based / market-based

47. What is my location-based Scope 2 result?
48. What is my market-based Scope 2 result?
49. Why are my location-based and market-based results different?
50. Which emission factor was used for the location-based calculation?
51. Which supplier or contractual instrument supports the market-based result?
52. What residual mix factor was used?
53. What grid region does the factor represent?
54. What year does the grid factor represent?
55. Is the factor supplier-specific or grid-average?
56. Which facilities have market-based evidence?
57. Which facilities are missing contractual or supplier-specific information?
58. Can you show the evidence supporting this Scope 2 factor?
59. What changed in Scope 2 because of a factor change rather than energy consumption?

The distinction between location-based and market-based Scope 2 is an important accounting question. GHG Protocol describes location-based accounting as reflecting average grid emissions where consumption occurs, while market-based accounting reflects contractual/purchasing information and applicable supplier or residual-mix factors. citeturn1search68turn1search72

---

# 6. Scope 3 questions

GHG Protocol's Scope 3 framework covers 15 upstream and downstream categories. citeturn1search0turn1search4

### Overall Scope 3

60. What are my total Scope 3 emissions?
61. Which Scope 3 category contributes the most?
62. Which Scope 3 categories increased this year?
63. Which Scope 3 categories decreased?
64. Which categories are based on supplier-specific data?
65. Which categories use activity data?
66. Which categories use average-data methods?
67. Which categories use spend-based estimates?
68. Which categories have the weakest evidence?
69. Which categories have the largest uncertainty?
70. Which categories should I prioritize for better primary data?
71. Which suppliers are driving Scope 3?
72. Which Scope 3 results are directly supported by supplier information?
73. How much of Scope 3 comes from estimated data?
74. What changed in Scope 3 compared with last year?

---

# 7. Scope 3 Category 1 — Purchased Goods and Services

75. What are my Category 1 emissions?
76. Which purchased goods contribute most?
77. Which suppliers contribute most to Category 1?
78. Which purchased categories have the highest emissions?
79. Which Category 1 transactions are spend-based?
80. Which are activity-based?
81. Which are supplier-specific?
82. Which products have supplier-specific emission factors?
83. What factor was applied to this purchase?
84. Why was this supplier/product assigned this factor?
85. Can you show the invoice line behind this calculation?
86. What percentage of Category 1 uses primary supplier data?
87. Which Category 1 suppliers have not provided data?
88. What would improve the accuracy of Category 1 most?

GHG Protocol's Category 1 guidance explicitly distinguishes supplier-specific, hybrid, average-data and spend-based approaches, and recommends collecting supplier methodology, factor/GWP information, assurance status and primary/secondary-data proportions where relevant. citeturn1search69turn1search71

---

# 8. Scope 3 Category 2 — Capital Goods

89. What are my Capital Goods emissions?
90. Which capital purchases contribute most?
91. Which suppliers contribute most?
92. Which capital-goods calculations are spend-based?
93. Which use activity or product data?
94. Which factor was used for this capital purchase?
95. Can you show the source transaction and calculation?

---

# 9. Category 3 — Fuel- and Energy-Related Activities

96. What are my Category 3 emissions?
97. Which fuels or energy sources contribute most?
98. Which upstream emissions are associated with my electricity consumption?
99. Which factor was used for upstream fuel/energy emissions?
100. Which energy sources have the highest upstream impact?
101. What evidence supports the activity data?

---

# 10. Category 4 — Upstream Transportation and Distribution

102. What are my upstream transportation emissions?
103. Which carriers contribute most?
104. Which routes contribute most?
105. Which transport modes contribute most?
106. What tonne-kilometres or other activity data were used?
107. Which transport emission factor was used?
108. Which shipments were estimated?
109. Can you trace this transport result to the source record?

---

# 11. Category 5 — Waste Generated in Operations

110. What are my waste emissions?
111. Which waste streams contribute most?
112. Which waste facilities/treatment methods contribute most?
113. What quantities of waste were used?
114. Which waste treatment factors were used?
115. Which waste records are estimated?
116. Can you show the source evidence?

---

# 12. Category 6 — Business Travel

117. What are my business-travel emissions?
118. Which travel mode contributes most?
119. Which routes contribute most?
120. Which travel records are based on distance?
121. Which records are spend-based?
122. Which emission factors were used for flights, rail, hotels or other travel?
123. What assumptions were used for missing travel information?
124. Can you show the underlying booking/expense evidence where available?

---

# 13. Category 7 — Employee Commuting

125. What are my employee-commuting emissions?
126. Which commuting modes contribute most?
127. What employee activity assumptions were used?
128. Which data is measured versus estimated?
129. Which factor was used?
130. What evidence supports the commuting calculation?

---

# 14. Category 8 — Upstream Leased Assets

131. What are my upstream leased-asset emissions?
132. Which leased assets contribute most?
133. Which facilities are included?
134. What activity data was used?
135. Which factor/method was used?
136. What is estimated versus measured?

---

# 15. Category 9 — Downstream Transportation and Distribution

137. What are my downstream transportation emissions?
138. Which carriers or routes contribute most?
139. Which transport modes contribute most?
140. What activity data supports the result?
141. Which factors were used?
142. Which records are estimated?

---

# 16. Category 10 — Processing of Sold Products

143. What are my emissions from processing sold products?
144. Which products contribute most?
145. Which downstream processes were included?
146. What activity data was used?
147. Which factors were applied?
148. What assumptions or estimates were used?

---

# 17. Category 11 — Use of Sold Products

149. What are my use-of-sold-products emissions?
150. Which products contribute most?
151. What expected lifetime/use assumptions were used?
152. Which energy/fuel consumption assumptions were used?
153. Which emission factors were used?
154. What evidence supports the assumptions?

---

# 18. Category 12 — End-of-Life Treatment of Sold Products

155. What are my product end-of-life emissions?
156. Which products contribute most?
157. Which disposal/recycling pathways were assumed?
158. What factors were used?
159. What percentage is based on actual versus estimated end-of-life data?

---

# 19. Category 13 — Downstream Leased Assets

160. What are my downstream leased-asset emissions?
161. Which leased assets contribute most?
162. Which tenants/assets are included?
163. What energy/activity data was used?
164. Which factors were used?
165. What assumptions are material?

---

# 20. Category 14 — Franchises

166. What are my franchise emissions?
167. Which franchises contribute most?
168. Which franchise locations are included?
169. What activity data was provided by franchisees?
170. Which results are estimated?
171. Which emission factors were used?
172. Which franchise data has supporting evidence?

---

# 21. Category 15 — Investments

173. What are my financed/investment-related emissions?
174. Which investments contribute most?
175. Which investees or asset classes drive the result?
176. What methodology was used?
177. What data quality is available?
178. Which investment emissions are estimated?
179. What source data supports the calculation?

Where financial-institution accounting is relevant, PCAF provides a separate global methodology for financed emissions, aligned with the GHG Protocol framework for Category 15. citeturn1search1

---

# 22. Supplier questions

180. Which suppliers generate the most Scope 3 emissions?
181. What are my top 10 suppliers by CO2e?
182. Which supplier's emissions increased the most?
183. Which suppliers have provided primary emissions data?
184. Which suppliers are still estimated using secondary factors?
185. Which suppliers have submitted emissions data for the current year?
186. Which suppliers' data is missing?
187. Which supplier records changed since the previous reporting period?
188. Which suppliers have the weakest evidence?
189. Which supplier emission factors are supplier-specific?
190. Which supplier factors are independently verified or assured, if recorded?
191. Which suppliers use primary versus secondary data?
192. What percentage of supplier data is primary?
193. Which supplier data is outside the reporting period?
194. Can you show me the supplier document supporting this emission?
195. What should I ask this supplier to improve the data?

Supplier-specific Scope 3 data can be materially more specific than generic averages; GHG Protocol guidance recommends collecting supplier methodology, data sources, emission factors, GWP information, assurance status and the proportion of primary data where applicable. citeturn1search69

---

# 23. Emission-factor questions

196. Which emission factor was used for this calculation?
197. What is the factor ID?
198. What is the factor value?
199. What unit is the factor expressed in?
200. Which factor database/source does it come from?
201. What year/vintage is the factor?
202. What geography does the factor represent?
203. Is the factor activity-based, spend-based, supplier-specific or another method?
204. What methodology produced the factor?
205. Which GWP assessment/reporting basis is associated with it, if recorded?
206. Has the factor been transformed or converted?
207. What was the original unit?
208. What unit conversion was applied?
209. Why was this factor selected?
210. Were other factors considered?
211. Is this a primary or secondary factor?
212. Is the factor current for the reporting year?
213. Did the factor change from the previous year?
214. How much of the emissions change is attributable to a factor change?
215. Can you show the authoritative factor record/source?
216. Does the factor's geography match the activity?
217. Does the factor's temporal coverage match the reporting period?
218. Does the factor's activity definition match the activity being calculated?

Emission-factor data systems commonly distinguish source, release year, geography, sector, activity type, transformation, quality and methodological metadata. Climatiq's public factor records, for example, expose source, geography, release year, sector, data type, quality flags and methodology metadata. citeturn1search7turn1search10

---

# 24. Calculation-method questions

219. How was this emission calculated?
220. What formula was used?
221. What activity data entered the calculation?
222. What unit conversion occurred?
223. Which factor was multiplied by the activity?
224. Was an allocation applied?
225. Was an estimate used?
226. Was a proxy used?
227. Was supplier-specific data used?
228. Was average-data methodology used?
229. Was spend-based methodology used?
230. Which methodology version was active when this calculation was created?
231. Can you reproduce the calculation from the stored snapshot?
232. Has this result been restated?
233. If it was restated, why?
234. What changed between the original and restated calculation?

---

# 25. Activity/input questions

235. What activity produced this emission?
236. What quantity was recorded?
237. What unit was recorded?
238. What reporting period does this activity cover?
239. Which facility/site does it belong to?
240. Which supplier/vendor does it relate to?
241. Which invoice/transaction produced it?
242. Which source document contains the input?
243. Which spreadsheet row contains the input?
244. Which spreadsheet sheet contains it?
245. Which PDF page contains it, where page-level provenance exists?
246. Was the value manually entered, extracted, or mapped?
247. Was OCR involved?
248. Was the value changed after extraction?
249. What was the original extracted value?
250. What mapped value was ultimately used?

---

# 26. Trend / variance / hotspot questions

251. Why did emissions increase this month?
252. Why did emissions decrease this month?
253. What changed compared with last month?
254. What changed compared with last year?
255. Which activities caused the largest increase?
256. Which activities caused the largest decrease?
257. Which factors changed?
258. Which activity volumes changed?
259. Which suppliers changed?
260. Which facilities changed?
261. Was the change caused by activity, factor, methodology, boundary or data availability?
262. Which emission source explains most of the variance?
263. What are the top five emission drivers?
264. What are the largest Scope 1 changes?
265. What are the largest Scope 2 changes?
266. What are the largest Scope 3 changes?
267. Which category is the largest hotspot?
268. Which supplier is the largest hotspot?

---

# 27. Data-quality questions

269. Which emissions records have missing evidence?
270. Which records have incomplete provenance?
271. Which records use estimated activity data?
272. Which records use secondary emission factors?
273. Which records use supplier estimates?
274. Which categories have the lowest data quality?
275. Which facilities have incomplete data?
276. Which reporting periods have missing data?
277. Which suppliers have incomplete submissions?
278. Which results depend on assumptions?
279. Which assumptions have the largest impact?
280. Which data should be upgraded from spend-based to activity-based?
281. Where do I have the largest evidence gaps?
282. Which records are most difficult to defend to an auditor?
283. What information is missing before this result can be independently checked?

---

# 28. Evidence / provenance questions

284. Where did this number come from?
285. Show me the source document.
286. Which invoice produced this number?
287. Which spreadsheet produced this number?
288. Which exact row produced this number?
289. Which sheet produced this number?
290. Which PDF page contains this value?
291. Which extracted value was used?
292. Which mapped value was used?
293. Which calculation snapshot produced the reported result?
294. Which report version contains this number?
295. Can I trace this result back to the original source?
296. What changed between the source and the final result?
297. Which evidence supports this emission factor?
298. Which evidence supports this classification?
299. Which evidence supports this supplier's result?
300. Is there an audit trail for this change?
301. Who changed the record?
302. When was it changed?
303. What was changed?
304. Is the evidence still available?

The traceability pattern is also visible in current carbon/sustainability products: Pulsora describes tracing figures to source, calculation, subsidiary/facility and approval trail, while scoped describes linking data points to invoices, meter readings or supplier documents and maintaining a calculation trace. citeturn0search6turn0search0

---

# 29. External auditor questions

These are especially important because the auditor is **not a CarbonTally platform user**. CarbonTally Insight should only answer these from evidence that the customer has authorized and that CarbonTally actually holds.

305. What is the source of this reported number?
306. Can you reproduce the calculation?
307. What activity data supports this number?
308. What emission factor supports this number?
309. Where did that factor come from?
310. What year/version is the factor?
311. What geography does the factor represent?
312. What methodology was used?
313. What organizational boundary applies?
314. What operational boundary applies?
315. What reporting period does this evidence cover?
316. Is the source data primary or secondary?
317. What percentage of the calculation uses primary data?
318. What assumptions were used?
319. Which assumptions are material?
320. Which calculations were estimated?
321. Which records were manually adjusted?
322. Who approved the adjustment?
323. When was the adjustment made?
324. What changed after the original calculation?
325. Was there a restatement?
326. Why was the restatement made?
327. Which factor was used before and after the restatement?
328. Which records are missing evidence?
329. Which Scope 3 categories are incomplete?
330. Which supplier data is missing?
331. Which suppliers provided primary data?
332. Which supplier factors are verified/assured, if recorded?
333. Can you trace this reported total to the underlying source records?
334. Can you provide the evidence chain for this sample?
335. Does the evidence cover the same reporting period as the inventory?
336. Which records are based on estimates?
337. What is the basis for those estimates?
338. Which methodology version was used?
339. Which factor database was used?
340. Can you show the factor metadata?
341. Can you show the calculation snapshot?
342. Can you show the source document?
343. Can you show the exact line item?
344. Can you show the audit event associated with the change?

---

# 30. Consultant questions

345. Where are the client's largest emission hotspots?
346. Which Scope 3 categories need better primary data?
347. Which suppliers should be prioritized for data collection?
348. Which activities are currently spend-based?
349. Which could be upgraded to activity-based calculations?
350. Which supplier-specific factors are available?
351. Which factors have weak temporal or geographic representativeness?
352. Which records have incomplete evidence?
353. Which categories have the largest estimation dependence?
354. Which facilities have unusual year-over-year changes?
355. Which emissions changes are caused by activity volume?
356. Which are caused by factor changes?
357. Which are caused by methodology changes?
358. Which data should be reviewed before assurance?
359. Which source records support the reported hotspots?
360. Can you trace each major hotspot to its underlying evidence?
361. Which assumptions materially affect the inventory?
362. Which records should be sampled for manual review?
363. What changed since the previous reporting period?
364. Which results cannot currently be independently reproduced from stored evidence?

---

# 31. Boundary and methodology questions

365. What organizational boundary was used?
366. What operational boundary was used?
367. Which entities/facilities are included?
368. Which entities/facilities are excluded?
369. Why is this activity classified in this scope?
370. Why is this activity classified in this Scope 3 category?
371. What methodology was used for this category?
372. What calculation method was used?
373. What data-quality assumptions were used?
374. What exclusions were applied?
375. What changed in the boundary from the previous year?
376. Did the boundary change affect the trend?
377. Was a base year recalculated?
378. Why was the base year recalculated?
379. Which methodology version was used at the time?
380. Which methodology is used now?

---

# 32. Reporting / disclosure questions

381. What are my Scope 1, 2 and 3 totals for the reporting year?
382. What is the emissions intensity?
383. What denominator is used for the intensity metric?
384. Which entities are included in the reported total?
385. Which reporting framework does this result support?
386. Which disclosure is this number used for?
387. Which report version contains this number?
388. Which evidence supports the disclosure?
389. What data is missing from the disclosure?
390. Which values changed after the previous report?
391. Why did they change?
392. Which figures have been independently assured, if recorded?
393. What is the assurance status?
394. Which methodology note supports this disclosure?

CDP's emissions questionnaire materials, for example, ask for base-year Scope 1/2 emissions, the methodology/standard used, subsidiary-level breakdowns and verification/assurance status. citeturn0search95

---

# 33. Factor-selection challenge questions

These questions are particularly useful for consultants and auditors:

395. Why was this factor selected instead of another factor?
396. Does the factor match the activity definition?
397. Does the factor match the geography?
398. Does the factor match the reporting period?
399. Does the factor use the appropriate unit?
400. Is the factor supplier-specific or generic?
401. Is the factor primary or secondary?
402. What source published the factor?
403. What version was used at calculation time?
404. Has the source subsequently changed?
405. Was the factor transformed by CarbonTally?
406. What conversion was applied?
407. What GWP basis was used?
408. Is the factor CO2-only or CO2e?
409. Which gases are covered?
410. Does the factor have a known quality limitation?
411. What evidence supports its use?

Emission-factor metadata matters because factor sources can differ in geography, temporal representativeness, methodology, gases included, unit and transformation. Public factor databases expose these kinds of metadata and quality flags. citeturn1search7turn1search10turn1search14

---

# 34. Evidence-quality challenge questions

412. Is the source document original or derived?
413. Is the source document complete?
414. Does the evidence cover the entire reporting period?
415. Does the invoice/record match the calculated quantity?
416. Does the source unit match the calculation unit?
417. Can the extracted value be reconciled to the original document?
418. Can the mapped value be reconciled to the extracted value?
419. Can the calculation be reproduced from the stored snapshot?
420. Is there an evidence gap?
421. Is there a provenance gap?
422. Is there a missing source line?
423. Is the evidence from the correct entity/facility?
424. Is the evidence from the correct reporting period?
425. Is there evidence of manual intervention?
426. Is there an audit event for the intervention?

---

# 35. Questions Insight should answer with different evidence modes

Not every question needs the same response.

### Mode A — Authoritative numeric answer

Example:

> “What were my Scope 2 emissions in 2025?”

Expected answer basis:

- persisted CarbonTally records;
- deterministic aggregation;
- report/version context;
- evidence where appropriate.

### Mode B — Calculation explanation

Example:

> “Why was this calculation 20 kg CO2e?”

Expected answer basis:

- calculation snapshot;
- activity;
- quantity/unit;
- factor;
- methodology;
- provenance.

### Mode C — Evidence navigation

Example:

> “Show me the invoice line.”

Expected answer basis:

- source_item_id/source_line_item_id;
- authorized evidence route;
- Source Evidence Viewer.

### Mode D — Comparative analysis

Example:

> “Why did February increase?”

Expected answer basis:

- deterministic period comparison;
- explicit variance logic;
- component-level attribution.

### Mode E — Conceptual guidance

Example:

> “What is the difference between Scope 1 and Scope 2?”

Expected answer basis:

- governed carbon-accounting knowledge;
- clearly separated from customer-specific accounting data.

### Mode F — Audit challenge

Example:

> “Can you prove this number?”

Expected answer basis:

- calculation;
- factor;
- source;
- evidence lineage;
- audit record;
- limitations.

---

# 36. Questions that should trigger clarification rather than guessing

Insight should ask for clarification when a question is materially ambiguous.

Examples:

- “Why is my emissions high?”
- “Which supplier is the biggest?”
- “Why did emissions increase?”
- “Show me the invoice.”
- “What factor did you use?”

Potential clarification dimensions:

- reporting year;
- date range;
- scope;
- Scope 3 category;
- facility;
- supplier;
- report/version;
- activity;
- currency/unit;
- specific calculation.

---

# 37. Questions that must be answered with “no authoritative data found”

Examples:

- “What was supplier X's verified footprint?” when no supplier record exists.
- “Which invoice produced this number?” when the calculation has no resolvable evidence reference.
- “What factor was used?” when the historical snapshot does not retain factor information.
- “Who approved this factor?” when approval metadata is not stored.
- “What changed because of methodology?” when no comparable method history exists.

The system must not fill these gaps using generic LLM knowledge.

---

# 38. Important distinction: customer vs consultant vs external auditor

### Customer

Can ask about their own organization's authorized data.

### Consultant

May need broader analytical questions across the customer's authorized data, but access must be explicitly authorized by CarbonTally's access model.

### External auditor

Is not automatically a CarbonTally platform user.

If an auditor is not authenticated into CarbonTally, Insight should not expose customer data directly merely because the auditor asks a question.

The customer or authorized user should provide an evidence package, controlled report, export, or authorized evidence access path.

Therefore:

> **“Auditor question” describes the question CarbonTally should be able to support through a controlled evidence workflow; it does not automatically authorize an external auditor to query the customer's tenant.**

---

# 39. Industry patterns informing this library

Current carbon/sustainability platforms expose natural-language questions around:

- Scope 1/2/3;
- Scope 3 hotspots;
- supplier drivers;
- trends and comparisons;
- source traceability;
- data quality;
- reporting/disclosure gaps;
- methodology;
- emission factors;
- audit evidence.

Examples include:

- scoped's AI assistant covers GHG Protocol, Scope 1/2/3, emission factors, data quality and supplier engagement. citeturn0search2
- Pulsora demonstrates questions about Scope 2 source lineage, Scope 3 hotspots by supplier, weak data-quality categories, emissions trends and audit gaps. citeturn0search6
- Trace advertises questions such as top emission sources and suppliers driving Scope 3, with cited data-grounded responses. citeturn0search4
- Carbon Accounting AI emphasizes scope/category classification, supplier data, factor/method traceability and the distinction between screening estimates and audit-grade inventory. citeturn0search1turn0search10
- OCEANS emphasizes source, boundary, method, factor, assumption, version and review as the core elements of a traceable Scope 1–3 result. citeturn0search7

These are market observations, not evidence that CarbonTally currently implements the same capabilities.

---

# 40. Architecture implications for CarbonTally

This question library implies several distinct deterministic capability families:

### Existing / foundational

- calculation snapshot lookup;
- report lookup;
- report-version lookup;
- evidence lookup;
- source evidence navigation.

### Discovery

- find calculation by date;
- find by amount/result;
- find by activity;
- find by supplier;
- find by facility;
- find by scope/category.

### Aggregation

- total by scope;
- total by category;
- total by supplier;
- total by facility;
- total by activity;
- period comparisons.

### Explanation

- calculation explanation;
- factor explanation;
- methodology explanation;
- variance explanation.

### Data quality

- missing evidence;
- estimated records;
- secondary-factor usage;
- incomplete periods;
- supplier completeness;
- provenance completeness.

### Audit

- calculation reproducibility;
- evidence-chain resolution;
- factor provenance;
- change history;
- restatement history;
- approval history.

Each new capability requires its own deterministic data contract and explicit governance decision where it expands the closed I3/customer-tool surface.

---

# 41. Recommended product rule

The eventual Insight experience should be designed around:

## ASK → VERIFY → EXPLAIN → TRACE

### ASK
Understand what the user wants.

### VERIFY
Retrieve authoritative CarbonTally data using deterministic, authorized operations.

### EXPLAIN
Use the LLM to turn verified data into understandable language.

### TRACE
Give the user a path to the calculation/source/evidence supporting the answer.

This model is more appropriate for carbon accounting than a generic “chat with your database” approach because carbon results may be used for management decisions, disclosures, customer questionnaires and external assurance.

---

# 42. Governance reminder

This document is a **question library and product-design reference**.

It does NOT authorize:

- a fifth I3 tool;
- widening an existing I3 tool;
- unrestricted database access;
- new aggregation services;
- new Scope 1/2/3 calculation logic;
- new supplier analytics;
- new audit functionality;
- I7;
- full I8;
- production deployment.

Before implementation, each capability should be mapped to:

1. existing authorized contract;
2. existing backend capability;
3. required new deterministic capability;
4. required authorization;
5. acceptance criteria;
6. independent verification.

---

## 43. Core principle

CarbonTally Insight should eventually be able to answer the questions that a serious carbon-accounting customer, consultant or external auditor would ask — **but only to the extent that CarbonTally can substantiate the answer.**

A truthful:

> “I cannot verify that from the evidence currently stored.”

is preferable to a plausible but unsupported answer.
