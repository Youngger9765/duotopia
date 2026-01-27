import OrgLandingPage from '@/pages/public/org-landing/OrgLandingPage';

// 在你的路由配置中新增：
// import { OrgLandingPage } from '@/pages/public/org-landing';

// 在 Router 中新增路由：
export const orgLandingRoute = {
  path: '/org-landing',
  element: <OrgLandingPage />,
};

// 或者在 react-router v6 中：
/*
<Route path="/org-landing" element={<OrgLandingPage />} />
*/

export default OrgLandingPage;
