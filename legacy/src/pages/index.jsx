import Layout from "./Layout.jsx";

import Statistics from "./Statistics";

import TeacherDashboard from "./TeacherDashboard";

import StudentPractice from "./StudentPractice";

import PracticeDetail from "./PracticeDetail";

import StudentDashboard from "./StudentDashboard";

import SchoolManagement from "./SchoolManagement";

import ListeningCloze from "./ListeningCloze";

import SentenceMaking from "./SentenceMaking";

import SpeakingPractice from "./SpeakingPractice";

import SpeakingQuizzes from "./SpeakingQuizzes";

import AssignHomework from "./AssignHomework";

import Assignments from "./Assignments";

import GradingDashboard from "./GradingDashboard";

import Portal from "./Portal";

import { BrowserRouter as Router, Route, Routes, useLocation } from 'react-router-dom';

const PAGES = {
    
    Statistics: Statistics,
    
    TeacherDashboard: TeacherDashboard,
    
    StudentPractice: StudentPractice,
    
    PracticeDetail: PracticeDetail,
    
    StudentDashboard: StudentDashboard,
    
    SchoolManagement: SchoolManagement,
    
    ListeningCloze: ListeningCloze,
    
    SentenceMaking: SentenceMaking,
    
    SpeakingPractice: SpeakingPractice,
    
    SpeakingQuizzes: SpeakingQuizzes,
    
    AssignHomework: AssignHomework,
    
    Assignments: Assignments,
    
    GradingDashboard: GradingDashboard,
    
    Portal: Portal,
    
}

function _getCurrentPage(url) {
    if (url.endsWith('/')) {
        url = url.slice(0, -1);
    }
    let urlLastPart = url.split('/').pop();
    if (urlLastPart.includes('?')) {
        urlLastPart = urlLastPart.split('?')[0];
    }

    const pageName = Object.keys(PAGES).find(page => page.toLowerCase() === urlLastPart.toLowerCase());
    return pageName || Object.keys(PAGES)[0];
}

// Create a wrapper component that uses useLocation inside the Router context
function PagesContent() {
    const location = useLocation();
    const currentPage = _getCurrentPage(location.pathname);
    
    return (
        <Layout currentPageName={currentPage}>
            <Routes>            
                
                    <Route path="/" element={<Statistics />} />
                
                
                <Route path="/Statistics" element={<Statistics />} />
                
                <Route path="/TeacherDashboard" element={<TeacherDashboard />} />
                
                <Route path="/StudentPractice" element={<StudentPractice />} />
                
                <Route path="/PracticeDetail" element={<PracticeDetail />} />
                
                <Route path="/StudentDashboard" element={<StudentDashboard />} />
                
                <Route path="/SchoolManagement" element={<SchoolManagement />} />
                
                <Route path="/ListeningCloze" element={<ListeningCloze />} />
                
                <Route path="/SentenceMaking" element={<SentenceMaking />} />
                
                <Route path="/SpeakingPractice" element={<SpeakingPractice />} />
                
                <Route path="/SpeakingQuizzes" element={<SpeakingQuizzes />} />
                
                <Route path="/AssignHomework" element={<AssignHomework />} />
                
                <Route path="/Assignments" element={<Assignments />} />
                
                <Route path="/GradingDashboard" element={<GradingDashboard />} />
                
                <Route path="/Portal" element={<Portal />} />
                
            </Routes>
        </Layout>
    );
}

export default function Pages() {
    return (
        <Router>
            <PagesContent />
        </Router>
    );
}