/**
 * Manual Organization UI Test
 *
 * Run this to manually test the organization login flow
 *
 * Usage:
 * npx ts-node tests/manual-org-test.ts
 */

async function testOrgOwnerLogin() {
  const baseUrl = 'http://localhost:8000';

  console.log('🔍 Testing org_owner login flow...\n');

  // Step 1: Login
  console.log('Step 1: Login as owner@duotopia.com');
  const loginResponse = await fetch(`${baseUrl}/api/auth/teacher/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'owner@duotopia.com',
      password: 'owner123',
    }),
  });

  if (!loginResponse.ok) {
    console.error('❌ Login failed:', await loginResponse.text());
    return;
  }

  const loginData = await loginResponse.json();
  console.log('✅ Login successful!');
  console.log(`   User: ${loginData.user.name} (${loginData.user.email})`);

  const token = loginData.access_token;

  // Step 2: Get roles
  console.log('\nStep 2: Fetching user roles');
  const rolesResponse = await fetch(`${baseUrl}/api/teachers/me/roles`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!rolesResponse.ok) {
    console.error('❌ Get roles failed:', await rolesResponse.text());
    return;
  }

  const rolesData = await rolesResponse.json();
  console.log('✅ Roles fetched successfully!');
  console.log(`   All roles: ${JSON.stringify(rolesData.all_roles)}`);
  console.log(`   Effective role: ${rolesData.effective_role}`);

  // Step 3: Check redirect logic
  console.log('\nStep 3: Checking redirect logic');
  const hasOrgRole = rolesData.all_roles.some((role: string) =>
    ['org_owner', 'org_admin', 'school_admin'].includes(role)
  );

  const expectedRedirect = hasOrgRole ? '/organization/dashboard' : '/teacher/dashboard';
  console.log(`✅ Expected redirect: ${expectedRedirect}`);

  if (hasOrgRole) {
    console.log('\n✅ TEST PASSED: User should be redirected to /organization/dashboard');
  } else {
    console.log('\n❌ TEST FAILED: User has no organization roles!');
    console.log(`   Roles found: ${JSON.stringify(rolesData.all_roles)}`);
  }

  // Step 4: Test teacher account
  console.log('\n\n🔍 Testing pure teacher login flow...\n');

  const teacherLoginResponse = await fetch(`${baseUrl}/api/auth/teacher/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'orgteacher@duotopia.com',
      password: 'orgteacher123',
    }),
  });

  if (!teacherLoginResponse.ok) {
    console.error('❌ Teacher login failed:', await teacherLoginResponse.text());
    return;
  }

  const teacherLoginData = await teacherLoginResponse.json();
  console.log('✅ Teacher login successful!');
  console.log(`   User: ${teacherLoginData.user.name} (${teacherLoginData.user.email})`);

  const teacherToken = teacherLoginData.access_token;

  const teacherRolesResponse = await fetch(`${baseUrl}/api/teachers/me/roles`, {
    headers: { 'Authorization': `Bearer ${teacherToken}` },
  });

  const teacherRolesData = await teacherRolesResponse.json();
  console.log('   All roles: ' + JSON.stringify(teacherRolesData.all_roles));

  const teacherHasOrgRole = teacherRolesData.all_roles.some((role: string) =>
    ['org_owner', 'org_admin', 'school_admin'].includes(role)
  );

  const teacherExpectedRedirect = teacherHasOrgRole ? '/organization/dashboard' : '/teacher/dashboard';
  console.log(`   Expected redirect: ${teacherExpectedRedirect}`);

  if (!teacherHasOrgRole) {
    console.log('\n✅ TEST PASSED: Pure teacher should be redirected to /teacher/dashboard');
  } else {
    console.log('\n❌ TEST FAILED: Teacher has unexpected organization roles!');
  }
}

testOrgOwnerLogin().catch(console.error);
