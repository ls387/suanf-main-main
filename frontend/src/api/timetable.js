import request from './index'

export const timetableApi = {
  // 教师课表
  getTeacherTimetable(params) {
    return request.get('/timetable/teacher', { params })
  },
  
  // 班级课表
  getClassTimetable(params) {
    return request.get('/timetable/class', { params })
  },
  
  // 教室课表
  getClassroomTimetable(params) {
    return request.get('/timetable/classroom', { params })
  },
  
  // 周课表
  getWeekTimetable(params) {
    return request.get('/timetable/week', { params })
  }
}

