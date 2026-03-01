import React from 'react';

// Define the shape of the data we expect from Person A's backend
interface ActionItem {
  title: string;
  assignee: string;
  deadline: string;
}

interface ActionItemListProps {
  items: ActionItem[];
}

export default function ActionItemList({ items }: ActionItemListProps) {
  // Empty State: What shows before any tasks are detected
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 text-gray-400">
        <svg className="w-8 h-8 mb-3 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <p className="font-medium text-sm">Listening for tasks...</p>
      </div>
    );
  }

  // Populated State: Map through the array and render the cards
  return (
    <div className="flex flex-col gap-4">
      {items.map((item, index) => (
        <div 
          key={index} 
          className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col gap-3 animate-in fade-in slide-in-from-right-4 duration-500"
        >
          <h3 className="font-semibold text-gray-800 text-lg leading-snug">
            {item.title}
          </h3>
          
          <div className="flex justify-between items-center text-sm pt-2 border-t border-gray-50">
            {/* Assignee Badge */}
            <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              {item.assignee}
            </span>
            
            {/* Deadline Badge */}
            <span className="bg-red-50 text-red-600 px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {item.deadline}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}