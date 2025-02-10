import xmind

def create_xmind_mindmap():
    # Load an existing workbook or create a new one if it doesn't exist.
    # If "example.xmind" does not exist, xmind.load() will create a new workbook.
    workbook = xmind.load("example.xmind")
    
    # Get the primary sheet and set its title.
    sheet = workbook.getPrimarySheet()
    sheet.setTitle("My Mind Map Example")
    
    # Get the root topic and set its title.
    root_topic = sheet.getRootTopic()
    root_topic.setTitle("Central Idea")
    
    # Create the first branch under the root topic.
    branch1 = root_topic.addSubTopic()
    branch1.setTitle("Branch 1")
    
    # Add subtopics under Branch 1.
    sub1 = branch1.addSubTopic()
    sub1.setTitle("Subtopic 1A")
    
    sub2 = branch1.addSubTopic()
    sub2.setTitle("Subtopic 1B")
    
    # Create the second branch under the root topic.
    branch2 = root_topic.addSubTopic()
    branch2.setTitle("Branch 2")
    
    # Add subtopics under Branch 2.
    sub3 = branch2.addSubTopic()
    sub3.setTitle("Subtopic 2A")
    
    sub4 = branch2.addSubTopic()
    sub4.setTitle("Subtopic 2B")
    
    # Save the workbook to a file.
    xmind.save(workbook, path="example.xmind")
    print("XMind mind map created and saved as 'example.xmind'.")

if __name__ == '__main__':
    create_xmind_mindmap()
