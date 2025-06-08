// frontend/src/components/DeliveryTool/components/GroupSelection.jsx

import React from 'react';

const GroupSelection = ({
  cleanedData,
  enabledGroups,
  setEnabledGroups,
  enabledDeliverables,
  setEnabledDeliverables
}) => {
  return (
    <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 mb-8">
      <h2 className="text-xl font-semibold text-white mb-4">3. Select Deliverable Groups</h2>

      <div className="mb-6 flex gap-3">
        <button
          onClick={() => {
            setEnabledGroups(new Set(cleanedData.deliverable_groups.map(g => g.groupTitle)));
            setEnabledDeliverables(new Set()); // Clear individual selections
          }}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white transition-colors"
        >
          Enable All Groups
        </button>
        <button
          onClick={() => {
            setEnabledGroups(new Set());
            setEnabledDeliverables(new Set());
          }}
          className="bg-neutral-600 hover:bg-neutral-500 px-4 py-2 rounded-lg text-white transition-colors"
        >
          Disable All
        </button>
      </div>

      <div className="space-y-4">
        {cleanedData.deliverable_groups.map((group, index) => {
          const isGroupEnabled = enabledGroups.has(group.groupTitle);
          const shippedCount = group.deliverables.filter(d => d.shipped).length;
          const totalCount = group.deliverables.length;
          const individualEnabledCount = group.deliverables.filter(d => enabledDeliverables.has(d.id)).length;

          return (
            <div key={index} className={`border rounded-lg p-4 transition-all ${
              isGroupEnabled ? 'border-blue-500 bg-blue-900/20' : 
              individualEnabledCount > 0 ? 'border-yellow-500 bg-yellow-900/20' :
              'border-neutral-500 bg-neutral-600'
            }`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={isGroupEnabled}
                    onChange={(e) => {
                      const newEnabledGroups = new Set(enabledGroups);
                      if (e.target.checked) {
                        newEnabledGroups.add(group.groupTitle);
                        // When enabling group, disable individual selections for this group
                        const newEnabledDeliverables = new Set(enabledDeliverables);
                        group.deliverables.forEach(d => newEnabledDeliverables.delete(d.id));
                        setEnabledDeliverables(newEnabledDeliverables);
                      } else {
                        newEnabledGroups.delete(group.groupTitle);
                      }
                      setEnabledGroups(newEnabledGroups);
                    }}
                    className="mt-1 h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div>
                    <h3 className="text-lg font-medium text-white">{group.groupTitle}</h3>
                    <div className="flex items-center gap-4 text-sm text-neutral-300 mt-1">
                      <span className="font-medium text-green-400">{totalCount} deliverables</span>
                      <span className="flex items-center gap-1">
                        <span className={`inline-block w-2 h-2 rounded-full ${
                          shippedCount === totalCount ? 'bg-green-400' : 
                          shippedCount > 0 ? 'bg-yellow-400' : 'bg-red-400'
                        }`}></span>
                        {shippedCount}/{totalCount} shipped
                      </span>
                      {!isGroupEnabled && individualEnabledCount > 0 && (
                        <span className="text-yellow-400">
                          {individualEnabledCount} selected individually
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm text-neutral-400">
                    Formats: {[...new Set(group.deliverables.map(d => d.suggested_slate_format))].join(', ')}
                  </div>
                </div>
              </div>

              {/* Deliverable Details */}
              <div className="ml-8 space-y-2">
                {group.deliverables.map((deliverable, deliverableIndex) => (
                  <div key={deliverableIndex} className="flex items-center justify-between bg-neutral-800/50 rounded p-3 text-sm">
                    <div className="flex items-center gap-3">
                      {/* Individual checkbox - only show when group is not enabled */}
                      {!isGroupEnabled && (
                        <input
                          type="checkbox"
                          checked={enabledDeliverables.has(deliverable.id)}
                          onChange={(e) => {
                            const newEnabledDeliverables = new Set(enabledDeliverables);
                            if (e.target.checked) {
                              newEnabledDeliverables.add(deliverable.id);
                            } else {
                              newEnabledDeliverables.delete(deliverable.id);
                            }
                            setEnabledDeliverables(newEnabledDeliverables);
                          }}
                          className="h-4 w-4 text-yellow-600 focus:ring-yellow-500 border-gray-300 rounded"
                        />
                      )}

                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        deliverable.shipped ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
                      }`}>
                        {deliverable.shipped ? 'Shipped' : 'Not Shipped'}
                      </span>
                      <span className="text-white font-medium">{deliverable.video_title}</span>
                      <span className="text-neutral-400">{deliverable.platform}</span>
                      <span className="text-neutral-400">{deliverable.duration}</span>
                      <span className={`px-2 py-1 rounded text-xs text-white ${
                        deliverable.suggested_slate_format === '16x9' ? 'bg-blue-600' :
                        deliverable.suggested_slate_format === '9x16' ? 'bg-green-600' :
                        deliverable.suggested_slate_format === '1x1' ? 'bg-purple-600' :
                        'bg-orange-600'
                      }`}>
                        {deliverable.suggested_slate_format}
                      </span>
                    </div>
                    <div className="text-neutral-400 text-xs">
                      {deliverable.ship_date} • {deliverable.slated_status}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default GroupSelection;