import {expect,test} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

const username=process.env.E2E_USERNAME||'phaseadmin';
const password=process.env.E2E_PASSWORD;
if(!password)throw new Error('Set E2E_PASSWORD to the generated local demo admin password before running browser tests.');
const sizes=[[1440,900],[1024,768],[390,844]] as const;
const screenshots=path.resolve(process.cwd(),'..','docs','screens','phase-4');
async function assertAccessible(page: import('@playwright/test').Page, route: string){
 const results=await new AxeBuilder({page}).analyze();
 const serious=results.violations.filter(item=>item.impact==='serious'||item.impact==='critical');
 expect(serious.map(item=>({id:item.id,impact:item.impact,help:item.help,nodes:item.nodes.map(node=>node.target)})),`${route} axe violations`).toEqual([]);
}

test('Phase 4 routes render and fit all required viewports',async({page})=>{
 test.setTimeout(120000);
 fs.mkdirSync(screenshots,{recursive:true});
 const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 page.on('console',message=>{if(message.type()==='error'&&!message.text().includes('401 (Unauthorized)'))errors.push(message.text())});
 await page.goto('/login');
 for(const [width,height] of sizes){
  await page.setViewportSize({width,height});
  await expect(page.getByText('SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.')).toBeVisible();
  await assertAccessible(page,'login');
  expect(await page.evaluate(()=>document.body.scrollWidth<=window.innerWidth&&getComputedStyle(document.documentElement).overflowX==='clip')).toBeTruthy();
  await page.screenshot({path:path.join(screenshots,`login-${width}x${height}.png`),fullPage:true});
 }
 await page.setViewportSize({width:1440,height:900});
 await page.getByLabel('Username').fill(username);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Sign in'}).click();
 await expect(page.getByRole('heading',{name:'Dashboard'})).toBeVisible();
 await page.goto('/admin?tab=simulator');await expect(page.getByRole('heading',{name:'Simulator controls'})).toBeVisible();await page.getByRole('button',{name:'Reset simulator'}).click();await page.getByRole('button',{name:'Confirm simulator reset'}).click();await expect(page.getByText(/Simulator reset with seed 42/)).toBeVisible();await page.goto('/dashboard');
 await expect(page.locator('.clinical-table tbody tr').first()).toBeVisible();
 const detailHref=await page.locator('.clinical-table tbody tr a').first().getAttribute('href');
 expect(detailHref).toBeTruthy();
 const routes:[string,string][]=[['dashboard','/dashboard'],['patients','/patients'],['patient-overview',detailHref!],['patient-monitoring',`${detailHref}?tab=monitoring`],['patient-labs',`${detailHref}?tab=labs`],['patient-timeline',`${detailHref}?tab=timeline`],['alerts','/alerts']];
 for(const [name,route] of routes){
  for(const [width,height] of sizes){
   await page.setViewportSize({width,height});await page.goto(route);
   await expect(page.getByRole('heading').first()).toBeVisible();
   await expect(page.locator('.skeleton')).toHaveCount(0);
   await expect(page.getByText('SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.')).toBeVisible();
   await page.waitForTimeout(250);
   expect(await page.evaluate(()=>document.body.scrollWidth<=window.innerWidth&&getComputedStyle(document.documentElement).overflowX==='clip'),`${name} at ${width}px has horizontal page overflow`).toBeTruthy();
   await page.screenshot({path:path.join(screenshots,`${name}-${width}x${height}.png`),fullPage:true});
   await assertAccessible(page,`${name} ${width}x${height}`);
  }
 }
 await page.goto('/patients?q=SIM-000007');
 const missingRow=page.getByRole('row').filter({hasText:'SIM-000007'});await expect(missingRow).toBeVisible();await missingRow.click();
 await expect(page.getByText('Assessment limited',{exact:true}).first()).toBeVisible();
 await page.goto('/patients?q=SIM-000009');
 const staleRow=page.getByRole('row').filter({hasText:'SIM-000009'});await expect(staleRow).toBeVisible();await staleRow.click();
 await expect(page.getByText('STALE',{exact:true}).first()).toBeVisible();
 await page.goto('/patients?q=SIM-000001');
 await page.getByRole('row').filter({hasText:'SIM-000001'}).click();
 await expect(page.getByRole('button',{name:'Save observation'})).toBeDisabled();
 await expect(page.getByText(/Observation entry requires a CLINICIAN/)).toBeVisible();
 const scenarios:[string,string,string][]=[['stable','SIM-000001','LOW'],['gradual deterioration','SIM-000003','LOW MEDIUM'],['sudden concerning change','SIM-000005','HIGH'],['missing observations','SIM-000007','Assessment limited'],['sensor disconnection','SIM-000009','STALE'],['data quality problems','SIM-000011','LOW']];
 for(const [scenario,patient,level] of scenarios){
  await page.goto(`/patients?q=${patient}`);
  await page.getByRole('row').filter({hasText:patient}).click();
  await expect(page.getByText(level,{exact:true}).first(),`${scenario} patient assessment`).toBeVisible();
 }
 await page.goto('/analytics');
 await expect(page.getByRole('row').filter({hasText:'Data quality problems'})).toContainText('4');
 await page.evaluate(()=>window.dispatchEvent(new Event('offline')));
 await expect(page.getByText(/Offline · showing last successful data update/)).toBeVisible();
 await page.evaluate(()=>window.dispatchEvent(new Event('online')));
 expect(errors,errors.join('\n')).toEqual([]);
});
